# Learning log

Written in the owner's own words. Entries marked TODO are prompts, not answers.

## Phase 2: evaluation harness

### Step 2.1: span-level scoring and synthetic data
Facts to build on (from Presidio's `RecognizerResult`): each detection has `entity_type`, `start`, `end`, `score`, and `intersects` counts overlapping characters (0 when spans only touch).

TODO (owner): in your own words,
1. What do precision and recall mean for a PII tool? Which error is worse, and why?
2. Why score at span level instead of per document or exact boundaries?
3. What can a small synthetic sample prove, and what can it not?
