# Plan: Phase 3, NZ identifier recognisers

Goal: detect the NZ identifiers Presidio misses (NHI, IRD, driver licence, NZ phone), validate with the issuer's checksum where one is published, and publish measured precision and recall for them using the Phase 2 harness.
Size: medium (about 1 to 1.5 weeks, ~450 changed lines, roughly half of it dataset). Branch: `phase-3-nz`. One commit per step; stop for approval after each. The diff passes 300 lines because the dataset is data and the three recognisers share one concern; the step commits keep each review small.
Evidence: `docs/research/nz-identifiers.md` (sources, algorithms, Presidio probe). Read it before 3.1. Nothing below invents a format that file did not confirm.

## Design decisions (state these in an ADR)
- **Scope: NHI, IRD, driver licence, NZ phone.** Postcode and address are out: no checksum, a bare 4-digit number is too ambiguous, and spaCy `LOCATION` already catches street and city names (research sections 3.5 and 4).
- **Validate, don't just pattern-match, where the issuer publishes a checksum.** NHI (both formats) and IRD get a pure `is_valid` function from the published algorithm. Licence and phone have no checksum, so they rely on pattern plus context words and will be less precise. Say so in the README.
- **A valid checksum means well-formed, not issued.** No claim of checking a real register.
- **Entity names:** `NZ_NHI`, `NZ_IRD`, `NZ_DRIVER_LICENCE`, following Presidio's `UK_NHS` and `AU_TFN` style. NZ phones stay `PHONE_NUMBER` so existing policies and the structured field map keep working.
- **Measure before building.** Write `eval/dataset_nz.jsonl` and record a baseline with the default analyzer before any recogniser exists. The gain is then measured, not asserted.
- **One analyzer builder.** Today `main.py` (lifespan) and `eval/run_eval.py` each call `AnalyzerEngine()`. A single factory in `core/` registers the NZ recognisers, so the eval measures what production runs.
- **Recognisers are classes only because Presidio requires it.** Keep the logic in pure module-level functions (checksum, normalise) with the class a thin wrapper. This honours the repo's "no classes unless a library requires them" rule.
- **Uppercase NHI only to start,** as the standard defines. Lowercase is a recorded limitation, revisited only if the eval shows it matters.
- **Phone approach decided by a measurement in 3.8,** not in advance: either add `NZ` to Presidio's `PhoneRecognizer` regions, or write a pattern recogniser from the ComCom structure. No new dependency either way (`phonenumbers` already ships with Presidio).

## Steps

| Step | Change | Done when |
|---|---|---|
| 3.1 | Learning note + ADR: why checksum validation, why this scope, why postcode and address are out, the NHI date conflict and why both formats are accepted. Read the Presidio docs on `PatternRecognizer` and `validate_result` first. | ADR written in your own words |
| 3.2 | `eval/dataset_nz.jsonl`, written before any recogniser. At least ~25 labeled spans per type (NHI current and new format, IRD 8 and 9 digit, licence, NZ phone in mobile, landline, `+64` and spaced forms). Include **look-alike negatives**: checksum-invalid NHI and IRD, other 9-digit and 8-character codes, years, amounts, 4-digit numbers. Synthetic only (see questions below). | a test checks every span slice is non-empty and offsets in range (extend `test_eval_dataset.py`, do not duplicate it) |
| 3.3 | Add `--dataset` and `--output` options to `eval/run_eval.py`. Run the **default** analyzer on the NZ dataset and commit the result as the baseline (`eval/results_nz_baseline.md`). | one command reproduces the baseline; the poor numbers are committed, not hidden |
| 3.4 | `core/analyzer_factory.py`: one function that builds the `AnalyzerEngine`; `main.py` and `run_eval.py` both call it. No behaviour change yet. | existing tests and Phase 2 eval numbers unchanged |
| 3.5 | `NZ_NHI`: pure `nhi_is_valid` (both formats, `I`/`O` excluded, remainder-0 rule for the current format, mod 23 for the new) + thin recogniser. | unit tests: the standard's two worked examples (`ZAC5361`, `ZBN77VL`), wrong check digit, `I`/`O` rejected, wrong length, remainder-zero case, each recogniser path (core target 100%) |
| 3.6 | `NZ_IRD`: pure `ird_is_valid` (range 10,000,000 to 200,000,000, 7 or 8 digit base, primary then secondary weights) + thin recogniser, with dash and space variants only if 3.2 data includes them. | unit tests: the spec's six worked examples, the 150M to 200M range boundary, secondary-weight path, check digit 10 twice, below-range rejected |
| 3.7 | `NZ_DRIVER_LICENCE`: 2 letters + 6 digits, low base score, raised only with context words ("licence", "license", "driver"). No checksum. | unit tests for pattern, context boost, and non-match on near-misses |
| 3.8 | NZ phone: spike both options against the baseline, keep the better, delete the other. Resolve the `UK_NHS` clash by checking that it cannot appear under an NZ policy. | PHONE_NUMBER NZ results measurably better than baseline; choice and numbers recorded in the ADR |
| 3.9 | Register the recognisers in the factory; add `config/examples/config.nz.yaml` requesting the NZ entities. One integration test: `/sanitize` under that policy redacts an NHI and an IRD in free text. | integration test passes; demo policy untouched |
| 3.10 | Rerun both datasets. Phase 2 numbers must not regress. README: NZ results table with n beside every number, the exact command, and a Limitations note. Update the `CLAUDE.md` "out of scope until planned" line and `docs/ARCHITECTURE.md` for the recogniser registry. | numbers in README match a fresh run; docs touched are updated |

## Honest-reporting rules
- Report the numbers you get, including poor ones. Low licence precision is a finding, not a failure.
- State the sample size beside every number. Fewer than ~20 labeled spans in a type: say it is an anecdote.
- Do not tune the dataset after seeing results. The baseline in 3.3 is committed before any recogniser exists.
- Report false alarms on the look-alike negatives separately. That is where checksum validation should show its value.
- Say what the checksum does not prove: a valid number is well-formed, not issued to anyone.
- NHI test data starts with `Z` only (the reserved test prefix), so the first-letter distribution is unrealistic. Note it as a limitation.

## Out of scope
Postcode and address recognisers, NZ passport, bank account, NZBN and other identifiers, structured-field-name mappings for NZ types, lowercase or typo-tolerant matching, te reo or other languages, checking numbers against a real register, resolving the NHI issuing-date conflict, LLM proxy, CI running the eval, rate-limit proxy-IP fix, pre-commit, dependency lockfile.

## Questions to settle before 3.2
- **Fictional phone numbers.** I did not find NZ's reserved fictional or drama number ranges in any source read. Find them in a primary source (Commerce Commission or the Numbering Administration Deed) before writing phone data; otherwise use only numbers that appear in the sources. Do not invent "safe" numbers.
- **Synthetic IRD numbers.** A checksum-valid number in the old range might belong to a real person. Interpretation, unverified: numbers from 150,000,001 to 200,000,000 were invalid until Feb 2026 so are probably not yet issued, which also exercises the new limit. Use the spec's worked examples plus numbers from that band, and state in the dataset notes that "unissued" is unconfirmed.
- **Synthetic licence numbers.** The pattern is not secret, but a random `AB123456` could match a real card. Accept that risk for letters and digits chosen to look artificial, and note it.
- **Where do the NZ entities live in policy?** Proposal: a new `config.nz.yaml` example, leaving `config.demo.yaml` untouched because the Phase 2 numbers depend on it.
- **Does an unknown entity name make `analyzer.analyze` raise in the installed Presidio?** If so, the 3.3 baseline requests only built-in types and scores the NZ labels as misses. Check at the start of 3.3.

## Skills
`/test-gap` after 3.6, `/scope-check` before the PR, `/phase-close` at the end. `/case-study` later draws on the baseline-versus-final numbers.

## Learning checkpoint (`docs/LEARNING.md`)
In your own words: what a checksum buys you and what it cannot (well-formed versus issued), why look-alike negatives matter more than extra positives, why a recogniser with no checksum (licence) needs context words and still ends up less precise, and what the sample sizes limit you to claiming.
