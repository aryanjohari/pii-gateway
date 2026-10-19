"""NZ National Health Index (NHI) number recogniser.

Format and check digit follow HISO 10046:2026 section 2.1 (Health NZ):
- current format AAANNNC: 3 letters, 3 digits, numeric check digit (modulus 11)
- new format AAANNAC: 3 letters, 2 digits, 1 letter, alphabetic check letter (modulus 23)
Letters exclude I and O. Both formats coexist, so both are accepted.
A passing check digit means the number is well-formed, not that it was ever issued.
"""

import re

from presidio_analyzer import Pattern, PatternRecognizer

NHI_ENTITY = "NZ_NHI"

# Alphabet without I and O; a letter's value is its 1-based position (A=1 ... Z=24).
_LETTERS = "ABCDEFGHJKLMNPQRSTUVWXYZ"
_WEIGHTS = (7, 6, 5, 4, 3, 2)
_LETTER = "[A-HJ-NP-Z]"
_CURRENT_FORMAT = f"{_LETTER}{{3}}[0-9]{{4}}"
_NEW_FORMAT = f"{_LETTER}{{3}}[0-9]{{2}}{_LETTER}{{2}}"
_CURRENT_RE = re.compile(_CURRENT_FORMAT)
_NEW_RE = re.compile(_NEW_FORMAT)
# Not preceded or followed by a letter or digit, so "XZAC5361" and "ZAC53611" do not match.
_NOT_EMBEDDED = r"(?<![A-Za-z0-9]){body}(?![A-Za-z0-9])"
_BASE_SCORE = 0.5
_CONTEXT_WORDS = ["nhi", "national health index", "health", "patient", "hospital", "clinic"]


def _weighted_sum(first_six: str) -> int:
    values = [_LETTERS.index(c) + 1 if c in _LETTERS else int(c) for c in first_six]
    return sum(value * weight for value, weight in zip(values, _WEIGHTS, strict=True))


def nhi_is_valid(candidate: str) -> bool:
    """True when `candidate` has a valid NHI shape and check character (upper case only)."""
    if _CURRENT_RE.fullmatch(candidate):
        total = _weighted_sum(candidate[:6])
        if total % 11 == 0:
            return False  # the standard marks this case invalid; no check digit can be issued
        check_digit = (11 - total % 11) % 11  # a result of 10 becomes 0
        return candidate[6] == str(check_digit)
    if _NEW_RE.fullmatch(candidate):
        # The standard gives index = 23 - (sum mod 23) and is silent on a remainder of 0;
        # we follow the formula as written, which maps it to index 23 (the letter Y).
        index = 23 - _weighted_sum(candidate[:6]) % 23
        return candidate[6] == _LETTERS[index - 1]
    return False


class NzNhiRecognizer(PatternRecognizer):
    """A class only because Presidio requires one; the logic lives in `nhi_is_valid`."""

    def __init__(self) -> None:
        super().__init__(
            supported_entity=NHI_ENTITY,
            patterns=[
                Pattern("nhi_current", _NOT_EMBEDDED.format(body=_CURRENT_FORMAT), _BASE_SCORE),
                Pattern("nhi_new", _NOT_EMBEDDED.format(body=_NEW_FORMAT), _BASE_SCORE),
            ],
            context=_CONTEXT_WORDS,
            supported_language="en",
            # Presidio's default adds IGNORECASE; the standard defines upper case only.
            global_regex_flags=re.DOTALL | re.MULTILINE,
        )

    def invalidate_result(self, pattern_text: str) -> bool | None:
        # Invalidate, don't validate: a failed check drops the match, while a passing
        # look-alike keeps its base score instead of being promoted to 1.0.
        return not nhi_is_valid(pattern_text)
