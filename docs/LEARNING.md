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

## Phase 4: LLM proxy

Answers are the owner's to write. The lines below are prompts only; the facts they point to are in `docs/plans/phase-4.md`, `docs/research/llm-api-formats.md` and the tests named in brackets.

### Step 4.1: design decisions (ADR still to be written)
TODO (owner): in your own words,
1. Why is "redact only, no restore" safer than putting the originals back into the reply? What new risk would a token map create?
2. What does "fail closed" mean for a proxy? Name two places in this code where it applies. [`test_redaction_failure_fails_closed`, `test_unsupported_requests_are_rejected_and_nothing_is_forwarded`]
3. Why must the upstream URL come from the environment and never from the request? What attack does that prevent (SSRF)?
4. What can the gateway see, and what can it not see? (Think about images, tool calls, `model`, and the model's reply.)
5. Why does the gateway accept only an allow-list of fields instead of forwarding unknown ones? What does that cost a user of Claude's `thinking` option?

### Steps 4.2 to 4.5: models, redaction, route, failures
TODO (owner): in your own words,
1. Why does `hide_input_in_errors` matter here, and why does the route also call `errors(include_input=False)`? [`test_error_text_does_not_echo_message_content`]
2. Why is `redact_texts` format-neutral, and what would adding a native Anthropic adapter need? [`test_output_matches_the_single_text_sanitizer`]
3. Why are upstream error bodies replaced with a gateway message, and what useful detail does that cost the caller? [`test_upstream_errors_keep_their_status_but_not_their_text`]
4. What protects a request from hanging forever, and what status does the caller see when it fires? [`test_upstream_timeout_gives_504_naming_the_upstream`]
5. Why does a shared HTTP client need cookies blocked? What would happen without it? [`test_upstream_cookies_are_not_replayed_to_later_callers`]
6. What bug did the NaN case show, and why did it fail closed even though it was a 500? [`test_non_finite_number_is_rejected_not_a_server_error`]

### Steps 4.6 to 4.8: worked example, docs, streaming
TODO (owner): in your own words,
1. Why did the clinic example need a separate policy file with `PERSON`, and what does the Maori-name probe in the README show about the limits? [`test_clinic_note_reaches_the_upstream_as_placeholders`]
2. What do the latency numbers measure, and what do they leave out? Why does cost grow with text length?
3. With `stream: true`, when does redaction happen relative to the first reply byte? What happens to the upstream request if the caller disconnects? [`test_caller_disconnect_closes_the_upstream_request`]
4. What can a stub-upstream test prove, and what can it not prove about a real provider?
5. Terms to define in this code's terms: server-sent events, SSRF, fail closed, allow-list.
