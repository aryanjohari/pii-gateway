# Learning log

Written in the owner's own words. Entries marked TODO are prompts, not answers.

## Phase 2: evaluation harness

### Step 2.1: span-level scoring and synthetic data
Facts to build on (from Presidio's `RecognizerResult`): each detection has `entity_type`, `start`, `end`, `score`, and `intersects` counts overlapping characters (0 when spans only touch).

TODO (owner): in your own words,
1. What do precision and recall mean for a PII tool? Which error is worse, and why?
2. Why score at span level instead of per document or exact boundaries?
3. What can a small synthetic sample prove, and what can it not?

## Phase 3: NZ identifier recognisers

### Step 3.1: checksums, look-alikes and what a recogniser can prove
Facts to build on (from `docs/research/nz-identifiers.md` and Presidio's `PatternRecognizer`): NHI and IRD numbers have published check digits; the driver licence and phone numbers do not. In Presidio, `validate_result` returning `True` sets a match's score to 1.0, `False` drops it, and `invalidate_result` returning `True` drops it while leaving other scores alone.

TODO (owner): in your own words,
1. What does a valid checksum prove about a number, and what does it not?
2. Why might `invalidate_result` be a better fit than `validate_result` for a number that can pass the checksum by chance? (Think about what score a random look-alike gets in each case.)
3. Why does the driver licence recogniser need context words, and why will it still be less precise than NHI and IRD?
4. Two sources disagree on when new-format NHI numbers start. Why is accepting both formats the right response, instead of picking one date?
