import pytest

from pii_gateway.core.recognizers.nz_ird import IRD_ENTITY, NzIrdRecognizer, ird_is_valid

# Worked examples from the Inland Revenue specification (appendix 5.1).
SPEC_VALID = ["49091850", "35901981", "49098576", "136410132"]


@pytest.mark.parametrize("number", SPEC_VALID)
def test_numbers_from_the_specification_are_valid(number: str) -> None:
    assert ird_is_valid(number)


def test_secondary_weights_are_used_when_the_first_check_digit_would_be_10() -> None:
    # 49098576 and 136410132 only pass through the secondary calculation (spec examples 3 and 4).
    assert ird_is_valid("49098576")
    assert not ird_is_valid("49098570")


def test_specification_example_with_the_wrong_check_digit_is_invalid() -> None:
    assert not ird_is_valid("136410133")


def test_zero_padded_nine_digit_form_used_in_ird_files_is_valid() -> None:
    # The IRD file specification pads an 8-digit number with a zero; its own sample is 010000289.
    assert ird_is_valid("010000289")


def test_number_below_the_lowest_valid_ird_number_is_invalid() -> None:
    assert not ird_is_valid("9125568")  # spec example 6
    assert ird_is_valid("10000009")
    assert not ird_is_valid("09125568")


def test_numbers_between_150_and_200_million_are_valid_since_the_2026_limit_change() -> None:
    assert ird_is_valid("180743146")
    assert ird_is_valid("199999990")  # largest valid number at the new limit


def test_numbers_above_200_million_are_invalid_even_with_a_correct_check_digit() -> None:
    assert not ird_is_valid("200000005")
    assert not ird_is_valid("200001001")


def test_check_digit_10_after_the_secondary_calculation_is_invalid() -> None:
    # Base 1000005 gives 10 with both weight sets, so no check digit can make it valid.
    assert not any(ird_is_valid(f"1000005{digit}") for digit in range(10))


@pytest.mark.parametrize(
    "value", ["", "1234567", "1234567890", "49-091-850", "4909185a", "４９０９１８５０"]
)
def test_wrong_shape_is_invalid(value: str) -> None:
    assert not ird_is_valid(value)


def _find(text: str) -> list[str]:
    results = NzIrdRecognizer().analyze(text, [IRD_ENTITY])
    return [text[r.start : r.end] for r in sorted(results, key=lambda r: r.start)]


def test_recogniser_finds_plain_and_grouped_valid_numbers() -> None:
    text = "IRD 49091850, 180743146, 168-507-968 and 159 597 857."
    assert _find(text) == ["49091850", "180743146", "168-507-968", "159 597 857"]


def test_recogniser_finds_a_grouped_eight_digit_number() -> None:
    assert _find("IRD number 49-091-850") == ["49-091-850"]


def test_grouped_numbers_score_higher_than_plain_ones() -> None:
    plain, grouped = (
        NzIrdRecognizer().analyze(text, [IRD_ENTITY])[0].score
        for text in ("180743146", "168-507-968")
    )
    assert (plain, grouped) == (0.3, 0.5)


def test_recogniser_drops_matches_with_a_wrong_check_digit() -> None:
    assert _find("180743147 and 168-507-969 and 136410133") == []


def test_recogniser_drops_numbers_outside_the_valid_range() -> None:
    assert _find("200001001 and 200000005") == []


@pytest.mark.parametrize("text", ["0219876543", "1807431461", "18074314612", "x1234567890"])
def test_recogniser_ignores_digits_inside_longer_numbers(text: str) -> None:
    assert _find(text) == []


def test_recogniser_does_not_treat_a_grouped_phone_prefix_as_an_ird_number() -> None:
    assert _find("Call 027 456 7890 or 021 987 6543") == []


@pytest.mark.parametrize("text", ["Call 099124008 now", "mobile 021 987 005", "ring 021987018"])
def test_recogniser_ignores_phone_shaped_digit_runs_even_when_the_check_digit_passes(
    text: str,
) -> None:
    # Each of these passes ird_is_valid by chance (about 1 in 10 landline-shaped strings does).
    digits = "".join(c for c in text if c.isdigit())
    assert ird_is_valid(digits)
    assert _find(text) == []


def test_recogniser_skips_the_zero_padded_form_even_though_it_is_a_valid_ird_number() -> None:
    # Trade-off recorded in ADR 0005: padded numbers come from IRD file uploads, not prose.
    assert ird_is_valid("049091850")
    assert _find("IRD 049091850") == []
