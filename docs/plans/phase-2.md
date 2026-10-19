# Plan: Phase 2, evaluation harness

Goal: replace "best-effort NLP" with measured precision and recall per entity type, published in the README. This is the biggest remaining gap (audit: Evidence of use = C).
Size: medium (about 1 week, ~250 changed lines, mostly data). Branch: `phase-2-eval`. One commit per step; stop for approval after each.

## Design decisions (state these in an ADR)
- **Evaluate the detector, not HTTP.** Call `analyzer.analyze` directly with the policy's entities, the same call `core/sanitize_text.py` makes. Faster, and it measures what we actually claim.
- **Synthetic, hand-written dataset.** Template sentences with labeled character spans. No real PII, no new dependency (no Faker). Public datasets are a later option; check licences first.
- **Span-level scoring:** a detection counts as a true positive if its entity type matches and it overlaps a labeled span. Report precision, recall and F1 per entity type, plus counts of misses and false alarms.
- **Not in the pytest run** (slow, loads spaCy). A small test checks the scorer math and that the dataset parses; the full run is `python -m eval.run_eval`.

## Steps

| Step | Change | Done when |
|---|---|---|
| 2.1 | Learning note + ADR: why span-level, why synthetic. Read the Presidio docs on `RecognizerResult` first. | ADR written in your own words |
| 2.2 | `eval/dataset.jsonl`: ~60–100 sentences, each `{text, spans:[{start,end,type}]}`. Cover EMAIL_ADDRESS, PERSON, PHONE_NUMBER, plus negatives (text with no PII). No NZ-specific content here (decided during 2.2): Phase 3 adds its own `eval/dataset_nz.jsonl` and reruns the same harness. | a test checks every span's text slice is non-empty and offsets are in range |
| 2.3 | `eval/scoring.py`: pure function (predicted spans, labeled spans) → per-type TP/FP/FN, precision, recall, F1. | unit tests: perfect match, a miss, a false alarm, a wrong type, overlap |
| 2.4 | `eval/run_eval.py`: loads the policy, builds the analyzer once, runs the dataset, prints a table and writes `eval/results.md`. Also report p50/p95 latency per sentence. | one command runs it; output reproducible (seeded or deterministic) |
| 2.5 | README: results table, dataset size, the exact command, and a Limitations note (synthetic data, small sample, English only). Replace "best-effort" with the measured numbers. | numbers in README match a fresh run |

## Honest-reporting rules
- Report the numbers you get, including poor ones. A low recall on NZ phones is a good finding, not a failure.
- State the sample size beside every number. Per-type results from fewer than ~20 examples are anecdotes; say so.
- Do not tune the dataset to make the score look better after seeing results. Write it before the first run.

## Out of scope
NZ recognisers (Phase 3), LLM-based detector, public datasets, web UI changes, CI running the eval, pre-commit, lockfile.

## Questions to settle before 2.2
- Which entities does the default policy request? Use the same list so the eval matches production.
- Where should `eval/` live (top-level folder vs `tests/`)? Proposal: top-level `eval/`, kept out of `src/` and out of the Docker image.

## Skills
`/test-gap` after 2.3, `/scope-check` before the PR, `/phase-close` at the end. `/case-study` later draws on the numbers.

## Learning checkpoint (`docs/LEARNING.md`)
In your own words: what precision vs recall means for a PII tool (which error is worse, and why), why span-level scoring, and what the sample size limits you can claim.
