"""NZ IRD (Inland Revenue) number recogniser.

An IRD number is 8 or 9 digits: a 7- or 8-digit base plus a trailing check digit, validated
with modulus 11 and a second set of weights when the first gives 10 (Inland Revenue file upload
specification, appendix 5.1). A passing check means the number is well-formed, not that it was
ever issued.
"""

import re

from presidio_analyzer import Pattern, PatternRecognizer

IRD_ENTITY = "NZ_IRD"

_PRIMARY_WEIGHTS = (3, 2, 7, 6, 5, 4, 3, 2)
_SECONDARY_WEIGHTS = (7, 4, 3, 2, 5, 2, 7, 6)
_LOWEST_IRD_NUMBER = 10_000_000
# The 2022 specification says 150,000,000; Inland Revenue raised the limit to 200,000,000
# on 10 Feb 2026 ("Increase to IRD number validation upper limit").
_HIGHEST_IRD_NUMBER = 200_000_000
_SEPARATORS = re.compile(r"[- ]")
_NOT_EMBEDDED = r"(?<![0-9]){body}(?![0-9])"
# The patterns never start with 0. IRD's file format pads an 8-digit number with a leading zero
# (`ird_is_valid` accepts that), but in free text a leading zero is far more likely a phone
# number such as 099124200, and about 1 in 10 of those would pass the check by chance.
# Scores are low because 8-9 digit numbers are common; the check digit does the real filtering.
_PLAIN_SCORE = 0.3
_GROUPED_SCORE = 0.5
_CONTEXT_WORDS = ["ird", "inland", "revenue", "tax", "payroll", "kiwisaver", "gst", "withholding"]


def _check_digit(base: str, weights: tuple[int, ...]) -> int:
    remainder = sum(int(digit) * weight for digit, weight in zip(base, weights, strict=True)) % 11
    return 0 if remainder == 0 else 11 - remainder


def ird_is_valid(digits: str) -> bool:
    """True when `digits` (digits only, no separators) is a valid IRD number."""
    if not re.fullmatch(r"[0-9]{8,9}", digits):
        return False
    if not _LOWEST_IRD_NUMBER <= int(digits) <= _HIGHEST_IRD_NUMBER:
        return False
    base = digits[:-1].zfill(8)
    check_digit = _check_digit(base, _PRIMARY_WEIGHTS)
    if check_digit == 10:
        check_digit = _check_digit(base, _SECONDARY_WEIGHTS)
        if check_digit == 10:
            return False
    return digits[-1] == str(check_digit)


class NzIrdRecognizer(PatternRecognizer):
    """A class only because Presidio requires one; the logic lives in `ird_is_valid`."""

    def __init__(self) -> None:
        super().__init__(
            supported_entity=IRD_ENTITY,
            patterns=[
                Pattern(
                    "ird_grouped",
                    _NOT_EMBEDDED.format(body="[1-9][0-9]{1,2}[- ][0-9]{3}[- ][0-9]{3}"),
                    _GROUPED_SCORE,
                ),
                Pattern(
                    "ird_nine_digits", _NOT_EMBEDDED.format(body="[1-9][0-9]{8}"), _PLAIN_SCORE
                ),
                Pattern(
                    "ird_eight_digits", _NOT_EMBEDDED.format(body="[1-9][0-9]{7}"), _PLAIN_SCORE
                ),
            ],
            context=_CONTEXT_WORDS,
            supported_language="en",
        )

    def invalidate_result(self, pattern_text: str) -> bool | None:
        # Invalidate, don't validate: see NzNhiRecognizer.
        return not ird_is_valid(_SEPARATORS.sub("", pattern_text))
