"""NZ driver licence number recogniser.

NZTA describes the licence number as 2 letters followed by 6 digits (for example AB123456).
No check digit is published, so this recogniser can only match the shape: any 2-letter + 6-digit
code looks the same, and only nearby context words ("licence", "driver") raise the score.
The licence "version number" printed on the card is a separate field and is not matched.
"""

import re

from presidio_analyzer import Pattern, PatternRecognizer

DRIVER_LICENCE_ENTITY = "NZ_DRIVER_LICENCE"

# Low on purpose: with no checksum, the shape alone is weak evidence.
_BASE_SCORE = 0.2
_LICENCE_SHAPE = r"(?<![A-Za-z0-9])[A-Z]{2}[0-9]{6}(?![A-Za-z0-9])"
_CONTEXT_WORDS = ["licence", "license", "driver", "driving", "dl", "nzta"]


class NzDriverLicenceRecognizer(PatternRecognizer):
    """A class only because Presidio requires one; there is no checksum logic to extract."""

    def __init__(self) -> None:
        super().__init__(
            supported_entity=DRIVER_LICENCE_ENTITY,
            patterns=[Pattern("nz_driver_licence", _LICENCE_SHAPE, _BASE_SCORE)],
            context=_CONTEXT_WORDS,
            supported_language="en",
            # Presidio's default adds IGNORECASE; licences are printed in upper case.
            global_regex_flags=re.DOTALL | re.MULTILINE,
        )
