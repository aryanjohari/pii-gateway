import pytest

from pii_gateway.core.recognizers.nz_nhi import NHI_ENTITY, NzNhiRecognizer, nhi_is_valid

# Worked examples printed in HISO 10046:2026 (the Z prefix is reserved for test numbers).
STANDARD_CURRENT = ["ZAC5361", "ZAA0067", "ZAL7848", "ZAS3128", "ZAB6427"]
STANDARD_NEW = ["ZBN77VL"]


@pytest.mark.parametrize("nhi", STANDARD_CURRENT + STANDARD_NEW)
def test_numbers_from_the_standard_are_valid(nhi: str) -> None:
    assert nhi_is_valid(nhi)


@pytest.mark.parametrize("nhi", ["ZAC5360", "ZAC5362", "ZBN77VM", "ZBN77VA"])
def test_wrong_check_character_is_invalid(nhi: str) -> None:
    assert not nhi_is_valid(nhi)


@pytest.mark.parametrize("nhi", ["ZIC5361", "ZOA0067", "ZBN77IL", "ZBN77OL"])
def test_letters_i_and_o_are_never_valid(nhi: str) -> None:
    assert not nhi_is_valid(nhi)


@pytest.mark.parametrize(
    "nhi",
    ["", "ZAC536", "ZAC53611", "zac5361", "zbn77vl", "1AC5361", "ZBN7V7L", "ZAC５３６１"],
)
def test_wrong_shape_is_invalid(nhi: str) -> None:
    assert not nhi_is_valid(nhi)


def test_current_format_with_zero_remainder_has_no_valid_check_digit() -> None:
    # ZAA004 has weighted sum 187 = 11 * 17; the standard says such a number is invalid.
    assert not any(nhi_is_valid(f"ZAA004{digit}") for digit in range(10))


def test_new_format_with_zero_remainder_follows_the_formula_as_written() -> None:
    # ZAA00P has weighted sum 207 = 9 * 23, so index 23 is the letter Y. The standard does not
    # spell this case out; this test records our reading of it (see docs/research unknown 6).
    assert nhi_is_valid("ZAA00PY")
    assert not nhi_is_valid("ZAA00PA")


def _find(text: str) -> list[str]:
    results = NzNhiRecognizer().analyze(text, [NHI_ENTITY])
    return [text[r.start : r.end] for r in results]


def test_recogniser_finds_valid_numbers_in_both_formats() -> None:
    assert _find("Patient NHI: ZAC5361 and new-format ZBN77VL.") == ["ZAC5361", "ZBN77VL"]


def test_recogniser_returns_base_score_not_full_confidence() -> None:
    (result,) = NzNhiRecognizer().analyze("NHI ZAC5361", [NHI_ENTITY])
    assert result.entity_type == NHI_ENTITY
    assert result.score == 0.5


def test_recogniser_drops_matches_with_a_wrong_check_digit() -> None:
    assert _find("Rejected NHI ZAC5360 and ZBN77VM.") == []


def test_recogniser_ignores_lowercase() -> None:
    assert _find("nhi zac5361") == []


@pytest.mark.parametrize("text", ["XZAC5361", "ZAC53611", "ZAC5361Q"])
def test_recogniser_ignores_numbers_embedded_in_longer_codes(text: str) -> None:
    assert _find(text) == []


def test_recogniser_matches_at_punctuation_and_underscore_boundaries() -> None:
    # An underscore counts as a separator (field names, logs): a missed NHI costs more than a match.
    assert _find("(ZAC5361), ZBN77VL. nhi_ZAC5361") == ["ZAC5361", "ZBN77VL", "ZAC5361"]
