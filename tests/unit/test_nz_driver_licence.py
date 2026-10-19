import pytest

from pii_gateway.core.recognizers.nz_driver_licence import (
    DRIVER_LICENCE_ENTITY,
    NzDriverLicenceRecognizer,
)


def _find(text: str) -> list[str]:
    results = NzDriverLicenceRecognizer().analyze(text, [DRIVER_LICENCE_ENTITY])
    return [text[r.start : r.end] for r in sorted(results, key=lambda r: r.start)]


def test_finds_two_letters_followed_by_six_digits() -> None:
    assert _find("Driver licence number AB123456 expires in 2028.") == ["AB123456"]


def test_finds_several_numbers_and_ones_next_to_punctuation() -> None:
    assert _find("(AB123456), CD654321; licence EF111222.") == ["AB123456", "CD654321", "EF111222"]


def test_returns_a_low_base_score() -> None:
    (result,) = NzDriverLicenceRecognizer().analyze("AB123456", [DRIVER_LICENCE_ENTITY])
    assert result.entity_type == DRIVER_LICENCE_ENTITY
    assert result.score == 0.2


@pytest.mark.parametrize(
    "text",
    ["A123456", "ABC12345", "AB12345", "AB1234567", "AB12345A", "12ABCD34", "ab123456", "Ab123456"],
)
def test_ignores_other_shapes_and_lowercase(text: str) -> None:
    assert _find(text) == []


@pytest.mark.parametrize("text", ["XAB123456", "AB123456X", "AB1234567", "ABC123456"])
def test_ignores_codes_embedded_in_longer_strings(text: str) -> None:
    assert _find(text) == []


def test_cannot_tell_a_part_number_from_a_licence() -> None:
    # Known limitation, recorded in ADR 0005: with no checksum any 2-letter + 6-digit code
    # matches, whatever the surrounding words say. Only the score changes with context.
    assert _find("Part number HP851871 is out of stock.") == ["HP851871"]
