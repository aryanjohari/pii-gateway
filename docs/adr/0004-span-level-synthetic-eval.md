# ADR 0004: Evaluate the detector with span-level scoring on a synthetic dataset

- Status: Draft (skeleton by Claude, to be rewritten in the owner's words)

## Context
The README says redaction is "best-effort". That claim cannot be checked. Phase 2 adds a harness that reports precision and recall per entity type.

Presidio's `AnalyzerEngine.analyze` returns `RecognizerResult` objects with `entity_type`, `start`, `end` (character offsets) and `score`. `RecognizerResult.intersects` returns the number of overlapping characters, and 0 when two spans only touch. Scoring can therefore work on character spans.

## Decision
- **Evaluate the detector, not HTTP.** The harness calls `analyzer.analyze(text, language="en", entities=...)`, the same call `core/sanitize_text.py` makes. It measures what the product relies on and runs faster than going through the API.
- **Same entities as production.** `config.example.yaml` requests `EMAIL_ADDRESS`, `PERSON`; `config.demo.yaml` also requests `PHONE_NUMBER`. There is no single default, so the harness uses the demo policy list (the superset) and the README says so.
- **Span-level scoring.** A prediction is a true positive if its entity type matches a labeled span and the two overlap by at least one character (`intersects > 0`). An unmatched prediction is a false positive; an unmatched labeled span is a false negative.
- **Synthetic, hand-written dataset.** Template sentences with labeled character offsets. No real PII, no new dependency, no licence questions. It is written before the first run and is not tuned afterwards.
- **Outside pytest, outside `src/`.** The harness lives in top-level `eval/`, runs with `python -m eval.run_eval`, and is not in the Docker image. Only the scorer math and dataset validity are tested in pytest, because loading spaCy is slow.

## Consequences
- Overlap matching ignores harmless boundary differences (a trailing space, a title like "Dr"). The cost is that an over-wide detection still scores as correct, so recall is flattering for boundary quality.
- Synthetic templates are cleaner than real text, so scores are optimistic. They are a baseline and a regression guard, not a claim about production data.
- Every number is reported with its sample size. A per-type result from fewer than ~20 examples is an anecdote.
- Same-type neighbours (two names in a row) can both match one labeled span; the scorer must define how that is counted (settled in step 2.3).
- English only, so NZ phone formats and Māori names are likely baseline gaps. That is a finding, and it motivates Phase 3.

## Alternatives considered
- **Exact-boundary matching:** stricter, but penalises differences that do not change what gets redacted. Could be added later as a second number.
- **Document-level scoring:** simple, but hides which entity type fails.
- **Public datasets:** more realistic, but need licence checks and may contain real PII. A later option.
- **Faker-generated data:** easy volume, but adds a dependency and produces unrealistic NZ formats.
