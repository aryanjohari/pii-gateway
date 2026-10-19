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

### Phase 5 Part A: hardening (5.1 to 5.5)
TODO (owner): in your own words,
1. Why must `TRUSTED_PROXY_HEADER` be opt-in? What can a caller do if the app trusts the header by default, or if the app is reachable around the proxy? [`test_rate_limit_ignores_proxy_header_by_default`]
2. What does `constraints.txt` protect against, and what does it not (think of the spaCy model, and a package that is new in `pyproject.toml`)? Why a constraints file over `uv.lock` here?
3. Why does `web/` have its own workflow with a path filter, and why is `npm run lint` still broken?
4. What does a pre-commit hook catch that CI also catches, and why have both?
5. What did the `file_ingest` dedupe change, and which tests would have caught a behaviour change?

## Phase 6: a demo that explains itself

Answers are the owner's to write. The lines below are prompts only; the facts they point to are in `docs/plans/phase-6.md`, `web/DESIGN.md` and the tests named in brackets.

### Steps 6.1 and 6.2: audit fixes and design
TODO (owner): in your own words,
1. Why does a result need a live region (`role="status"`), and what would a screen-reader user have heard without it? [`Playground.test.tsx`, "shows both panels and announces what was removed"]
2. Why is `outline-none` on an input a WCAG failure unless something replaces it? What replaced it here?
3. `config.nz.yaml` and `config.demo.yaml` each had half of what the playground needed. What went wrong with each, and why a new file (`config.demo-nz.yaml`) instead of editing `config.demo.yaml`?

### Step 6.3: the redesign
TODO (owner): in your own words,
1. The API returns counts but no offsets. How does `markRedactions` still show what was removed, and when does it return `null`? [`markRedactions.test.ts`]
2. What is the risk if a removed span contains the text that follows it? Why is the limits note honest to say the highlights "may be off"?
3. Why does the UI show its own wording for errors instead of the server's message? [`Playground.test.tsx`, "shows our wording for a rate limit"]
4. Why does the response get checked at the boundary (`parseSanitizeResponse`) instead of cast with `as`?
5. The "too long" limit lives in three places. What keeps them in step, and what happens if they drift?

### Step 6.4: tooling and tests
TODO (owner): in your own words,
1. Why did `next lint` fail, and what does `npm run lint` run now?
2. What did axe find in the first browser run, and why can axe never prove a page is accessible? What still needs a person?
3. Why do the browser tests set reduced motion, and what would a false alarm look like without it?
4. Why mock only `fetch` in the component tests? Which part of the system does the offline Playwright test exercise that the mocked one does not?
5. Why is `npm audit` limited to production dependencies in CI?
6. Terms to define in this code's terms: live region, focus-visible, WCAG 2.2 AA, axe-core, scrollable region.
