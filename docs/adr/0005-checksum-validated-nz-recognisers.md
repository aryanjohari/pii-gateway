# ADR 0005: NZ identifier recognisers validated by the issuer's checksum

- Status: Draft (skeleton by Claude, to be rewritten in the owner's words)

## Context
Presidio 2.2.364 has no NZ recogniser. A probe of the default analyzer (11 synthetic strings, an anecdote) found NHI numbers and postcodes undetected, an NZ mobile flagged `UK_NHS` at 1.0, and a licence-shaped string flagged `US_DRIVER_LICENSE`. Evidence and sources: `docs/research/nz-identifiers.md`.

Two NZ identifiers publish a checksum: the NHI number (HISO 10046:2026, section 2.1.4, two formats) and the IRD number (Inland Revenue spec, valid range raised to 200,000,000 on 10 Feb 2026). The driver licence number (2 letters + 6 digits) and NZ phone numbers have a known shape but no checksum.

How Presidio treats a pattern recogniser's result (read in `pattern_recognizer.py`, installed version):
- `validate_result(text)` returning `True` sets the score to 1.0; `False` sets it to 0 and the match is dropped; `None` leaves the pattern's own score.
- `invalidate_result(text)` returning `True` sets the score to 0 and the match is dropped; otherwise the score is untouched.

## Decision
- **Scope: NHI, IRD, driver licence, NZ phone.** Postcode and address are out: no checksum, a bare 4-digit number is ambiguous, and spaCy `LOCATION` already catches street and city names.
- **Entity names:** `NZ_NHI`, `NZ_IRD`, `NZ_DRIVER_LICENCE`, in the style of `UK_NHS` and `AU_TFN`. NZ phones stay `PHONE_NUMBER` so existing policies keep working.
- **Checksum logic lives in pure functions** (`nhi_is_valid`, `ird_is_valid`), unit tested on their own. The Presidio recogniser class is a thin wrapper, because Presidio requires a class.
- **Use `invalidate_result`, not `validate_result`, to apply the checksum.** *(Proposal, to be confirmed against the 3.5/3.6 tests.)* A failed checksum drops the match, which removes most look-alikes. A passed checksum keeps the pattern's own score, so a random 9-digit number that happens to pass is not promoted to 1.0 and context words ("IRD", "tax number") can still raise real ones. Using `validate_result` would give every passing look-alike a score of 1.0.
- **A valid checksum means well-formed, not issued.** The product does not check any register and must not say it does.
- **Accept both NHI formats.** The standard says new-format numbers are issued from 1 July 2026; a Health NZ web page says 1 July 2027. The two formats coexist indefinitely, so the recogniser accepts both whichever date is right.
- **IRD range is 10,000,000 to 200,000,000.** The 2022 spec still says 150,000,000; the 2026 IRD notice supersedes it. The constant carries a comment naming the notice.
- **Driver licence: pattern plus context words, low base score.** There is no checksum to rely on.
- **Measure before building.** The NZ dataset and a default-analyzer baseline are committed before any recogniser exists (steps 3.2 and 3.3).
- **One analyzer builder** shared by the app and the eval, so the eval measures what production runs (step 3.4).

## Consequences
- NHI and IRD precision should be good because most look-alikes fail the checksum. By chance a random digit string will still pass some of the time; the look-alike negatives in the eval measure how often.
- Licence precision will be lower than NHI and IRD, and the README says so.
- NHI matching is uppercase-only to start (the standard defines upper case). Lowercase NHI numbers are a known gap.
- The test data cannot cover realistic NHI first letters: only the `Z` prefix is reserved for tests.
- The IRD "unissued numbers above 150,000,000" assumption for safe synthetic data is an interpretation, not confirmed.
- NZ phone data uses only four numbers, taken from illustrative examples in a Commerce Commission draft document, written in several formats. No primary source gave a reserved fictional range (the NAD allocation rules v7.1 use "reserved" only for code-block allocation). Those four may be real subscriber numbers, and the phone results measure format variety, not number variety.
- Driver licence numbers in the dataset are random letter-digit strings and could coincide with real cards; ones in the dataset were not checked against anything.
- `NZ_IRD` and the built-in `PHONE_NUMBER` can match the same IRD number. The analyzer returns both; the anonymizer keeps the higher score, so the text is redacted either way and only the label differs. With an IRD context word nearby `NZ_IRD` wins (0.85 against 0.75, or 0.65 against 0.4); without one a grouped number like `168-507-968` can be labelled `PHONE_NUMBER`. The eval scores each type separately and does not merge overlaps, so it still counts those as phone false alarms.
- Phone choice (extend Presidio's `PhoneRecognizer` regions versus a custom pattern) is deferred to a measurement in step 3.8 and recorded here afterwards.

## Alternatives considered
- **Pattern-only, no checksum:** simplest, but NHI and IRD shapes (letters + digits, 9 digits) match a lot of ordinary text.
- **Contributing an NZ module to Presidio upstream:** the right long-term home, but out of scope for a portfolio phase and slower to iterate.
- **Fuzzy or lowercase matching:** more recall, more false alarms, no evidence yet that it is needed.
- **Checking numbers against a real register:** not possible (no public register) and would send identifiers to a third party.
