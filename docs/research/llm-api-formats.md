# OpenAI chat-completions format for the Phase 4 proxy

Research, not legal advice. Access date for all sources: 2026-10-19. Feeds `docs/plans/phase-4.md`, step 4.0. Companion to `docs/research/nz-identifiers.md`.

## 1. Summary
- **The machine-readable spec is the best primary source.** `platform.openai.com` returned HTTP 403 to scripted requests (not bypassed), so the request, message, content-part and error schemas below come from OpenAI's own OpenAPI file (`openapi.json`, v2.3.0, last commit 2026-10-18) [S1].
- **`base_url` includes `/v1`; the client appends `/chat/completions`.** The gateway route `/v1/chat/completions` fits, and `LLM_UPSTREAM_BASE_URL` should be the full prefix (for example `https://api.openai.com/v1`).
- **More fields carry text than the plan lists.** Besides `messages[].content`, free text can sit in `name`, `prediction.content`, tool/function definitions, `response_format`, `stop`, `metadata` and `user`/`safety_identifier`. Step 4.1 must say which of these are scanned, rejected or passed through.
- **Assistant, tool and developer messages exist**, not only user/system. The history a client replays contains them, and they have different content rules (section 3.2).
- **Claude and Gemini both offer OpenAI-compatible endpoints** (section 7), so pointing `LLM_UPSTREAM_BASE_URL` at them may need no new gateway code. Anthropic calls its layer a testing aid, not a production path, and Google calls its support beta.
- **The Authorization question is answerable now:** SDKs always send `Authorization: Bearer <key>`, and the Python SDK also accepts extra custom headers. Both designs work; see section 5.

## 2. Frame and scope
- Product: self-hosted redaction gateway. Phase 4 adds a non-streaming, OpenAI-compatible `POST /v1/chat/completions` that redacts message text and forwards to an upstream.
- Decision supported: the 4.1 ADR (reject vs pass through), the 4.2 Pydantic models, the 4.4/4.5 error and auth behaviour.
- Covered: request body, message and content-part types, response object, error body, status codes, auth headers, `base_url` convention, streaming wire format (for the optional 4.8).
- Not covered (sections 1-6): Anthropic and Gemini, which are covered in section 7 (step 4.0b); the Responses API (`/v1/responses`, a different endpoint that clients may use instead; see Unknowns); Azure OpenAI and other "OpenAI-compatible" servers, which may differ from this spec; model-specific limits; OpenAI's data-retention terms; any claim about what the upstream does with data.
- Method: the OpenAPI JSON and SDK source were downloaded and parsed with a throwaway script (not committed). Fetched web pages were treated as data.

## 3. Findings

### 3.1 Endpoint, URL and auth
| Item | Finding | Source |
|---|---|---|
| Path and server | Operation `createChatCompletion`: `POST /chat/completions`, server URL `https://api.openai.com/v1`. | [S1] |
| Auth scheme | HTTP bearer: `Authorization: Bearer <key>`. | [S1] `securitySchemes` |
| SDK default base | Python SDK defaults to `https://api.openai.com/v1`, and reads `OPENAI_BASE_URL` if `base_url` is not passed. README example uses `base_url="http://my.test.server.example.com:8083/v1"`. | [S2] README, [S3] `_client.py` |
| SDK auth header | Python SDK builds `{"Authorization": f"Bearer {api_key}"}`; it also sends `OpenAI-Organization` and `OpenAI-Project` when configured, plus any custom headers the caller sets. | [S3] `default_headers`, `auth_headers` |
| Request id | Responses carry an `x-request-id` header that the SDK exposes as `_request_id`. | [S2] README |

### 3.2 Request body (`CreateChatCompletionRequest`) [S1]
Required: `model`, `messages`. Content type `application/json`.

**Message roles** (`ChatCompletionRequestMessage` is a union of six):

| Role | `content` | Notes |
|---|---|---|
| `developer` | string, or array of `text` parts (min 1) | `name` optional |
| `system` | string, or array of `text` parts | `name` optional |
| `user` | string, or array of parts: `text`, `image_url`, `input_audio`, `file` | `name` optional |
| `assistant` | string, array (`text` parts or one `refusal`), or null | null allowed only with `tool_calls` or `function_call`; also has `refusal`, `audio`, `tool_calls`, `function_call`, `name` |
| `tool` | string, or array of `text` parts | requires `tool_call_id` |
| `function` | string or null | deprecated role; requires `name` |

**Content parts:** `text` (`text`), `image_url`, `input_audio`, `file`, `refusal`. Text parts, and only text parts, hold scannable text. `text`, `image_url`, `input_audio` and `file` parts also accept an optional `prompt_cache_breakpoint` field.

**Other top-level fields:** `metadata`, `top_logprobs`, `temperature`, `top_p`, `safety_identifier`, `prompt_cache_key`, `prompt_cache_options`, `service_tier`, `modalities`, `verbosity`, `reasoning_effort`, `max_completion_tokens`, `frequency_penalty`, `presence_penalty`, `web_search_options`, `response_format` (text, json_schema, json_object), `audio`, `store`, `moderation`, `stream`, `stop` (string or up to 4 strings), `logit_bias`, `logprobs`, `n`, `prediction`, `stream_options`, `tools`, `tool_choice`, `parallel_tool_calls`. Deprecated but still in the schema: `user`, `max_tokens`, `seed`, `prompt_cache_retention`, `function_call`, `functions`.

**Fields that can hold free text (candidates for the 4.1 decision):**

| Field | What it holds | Interpretation for the proxy |
|---|---|---|
| `messages[].content` (string, text parts) | the prompt | Scan (the plan's v1 scope). |
| `messages[].name` | participant name; a person's name could go here | Plan says not scanned. Cheap to scan or reject; decide in 4.1. |
| `assistant.tool_calls`, `function_call`, `tool` message content | tool arguments and results; can contain data fetched about a person | Plan says reject tool calls. Note `tool` role messages carry text parts and would be present in any tool-using conversation. |
| `prediction.content` | predicted output text, typically a file being rewritten | Not in the plan. Can contain the same data as the prompt. |
| `tools[]`, `functions`, `response_format.json_schema` | function names, descriptions and JSON schemas | Usually developer-authored, rarely PII, but free text. Not in the plan. |
| `stop`, `metadata`, `user`, `safety_identifier`, `prompt_cache_key` | short strings; `user` and `safety_identifier` are meant to be end-user identifiers and could be an email | Not in the plan. Likely pass through; record the decision. |

### 3.3 Response (`CreateChatCompletionResponse`) [S1]
Required: `id`, `choices`, `created`, `model`, `object` (`"chat.completion"`). Optional: `usage`, `service_tier`, `metadata`, `moderation`, deprecated `system_fingerprint`. Each choice's message (`ChatCompletionResponseMessage`) has `role: "assistant"`, `content` (string or null), `refusal`, `tool_calls`, `annotations`, `audio`. Interpretation: because v1 forwards the body unchanged, the proxy can pass the upstream JSON through as-is rather than re-modelling it, which avoids dropping unknown fields.

### 3.4 Errors [S1], [S4]
- Body: `{"error": {"type", "message", "param", "code"}}`. All four keys are required; `param` and `code` may be null (`Error` schema).
- Statuses documented for this operation in the spec: 200, 400, 401, 403, 404, 429, 500, 503.
- The error-codes guide lists 400 (invalid `service_tier`), 401 (bad credentials), 403 (unsupported region), 429 (rate limit or quota), 500, 503 (overloaded). It shows no example JSON body [S4]; the body shape comes from the spec only.
- No 504 and no 422 appear in the spec. Interpretation: the gateway's own 504 (upstream timeout) and 422 (unsupported content) are gateway codes, not upstream ones. Returning them in the `{"error": {...}}` shape would let OpenAI SDKs parse them. That is a design choice for 4.5, not something the sources require.

### 3.5 Streaming (relevant only to optional 4.8) [S1]
`stream: true` returns `text/event-stream` of JSON chunk frames, ending with literal `data: [DONE]`. A failure after streaming has begun may arrive as a data frame holding an `error` object, and an interrupted stream may end without `[DONE]`. Until 4.8 ships, a request with `stream: true` needs defined behaviour (see implications).

## 4. Requirements table
| Rule (source + section) | Plain meaning | Applies? | Feature or test it implies | Priority | Confidence |
|---|---|---|---|---|---|
| [S1] `createChatCompletion` path + servers | Route is `{base}/chat/completions` where base ends in `/v1` | Yes | Route `/v1/chat/completions`; setting holds the upstream prefix including `/v1`; test the forwarded URL | High | High |
| [S1] `securitySchemes` | Upstream auth is a bearer token in `Authorization` | Yes | Forward caller's `Authorization` unchanged; test it reaches the fake upstream and never appears in logs | High | High |
| [S1] `ChatCompletionRequestMessage` | Six roles; assistant `content` may be null; user content may be string or parts | Yes | Pydantic union by `role`; tests: null assistant content with tool_calls, list-form user content | High | High |
| [S1] content-part schemas | Only `text` parts hold text; others are image, audio, file, refusal | Yes | Redact `text` parts; 422 with a code for `image_url`, `input_audio`, `file` (per plan recommendation) | High | High |
| [S1] request properties | Extra text-bearing fields exist (3.2) | Yes | Decide scan, reject or pass through for each in the ADR; one test per decision | High | High |
| [S1] `stream` | Streaming changes the response wire format | Yes | v1: reject `stream: true` with a 422 code rather than buffering silently; 4.8 reverses it | High | Medium (rejecting is my interpretation) |
| [S1] `Error` schema | OpenAI error body is `{"error": {type, message, param, code}}` | Yes | Gateway-generated errors on this route use the same shape; message carries upstream name and status, never message text | Medium | High (shape), Medium (SDK parse behaviour untested) |
| [S1] responses 400/401/403/404/429/500/503 | These are the upstream's own statuses | Yes | Pass upstream 4xx/5xx through with the gateway's added code; test one 429 and one 500 | Medium | High |
| [S3] `_client.py` | SDK sends only `Authorization` by default, but accepts custom headers | Yes | Settles the open auth question (section 5) | Medium | Medium (read in source, not in the README) |
| [S3] `default_headers` | SDK may send `OpenAI-Organization` / `OpenAI-Project` | Maybe | Decide whether to forward them; absent them, org-scoped keys may bill the wrong project | Low | Medium |

## 5. Product implications
- **Auth (settles plan question 3).** An SDK user can send the gateway key in a custom header (the Python SDK builds default headers from `_custom_headers` [S3]), so keeping `X-API-Key` for the gateway and forwarding `Authorization` upstream works for developers who control their client. It fails for tools that only expose an API-key field. Recommendation: keep `X-API-Key`, document the one-line SDK snippet, and revisit only if you want tools with a single key field. This is the simpler path and matches the existing `verify_http_auth`.
- **Upstream URL.** Env-only (as planned). Document that it must include `/v1`. Never take it from the request.
- **Build the models around the union, not a flat message.** A flat `{role, content: str}` would reject valid assistant/tool messages or silently drop fields.
- **Pass the response body through** rather than re-modelling it; it has many optional fields.
- **Wording to use:** "OpenAI-compatible", "tested against the OpenAI chat-completions format as documented on 2026-10-19". **Avoid:** "supports all OpenAI SDK features", "works with any OpenAI-compatible server" (not tested; other servers may differ).
- **README must say** the proxy covers `/chat/completions` only. Clients that call the Responses API are not covered (see Unknowns).

## 6. Unknowns and open questions
1. Does the OpenAI API reject or ignore unknown top-level request fields? The spec file I parsed was not checked for `additionalProperties`. Concrete test: send a request with a made-up field to a real endpoint (needs a key, so ask the owner), or inspect `additionalProperties` in the spec. Matters for whether the gateway should forward unknown fields.
2. How do the OpenAI Python and Node SDKs behave when the error body is not `{"error": {...}}`? Not verified. Matters for the 4.5 error shape. Test with the SDK against the fake upstream in 4.5.
3. Is the Responses API (`/v1/responses`) now the SDK's default for new code? If so, a developer who changes `base_url` may hit an endpoint the gateway does not serve. I did not check the current SDK guidance. Question for the owner: should the README only state the limit, or should this go on the roadmap?
4. Does `n > 1` or `logprobs` affect anything the proxy does? Assumed no (response is passed through); not verified.
5. Rate-limit and retry headers (`retry-after`, `x-ratelimit-*`): not read. Question: should 429 pass these through to the caller?
6. Should `OpenAI-Organization` and `OpenAI-Project` be forwarded? Needs an owner decision.
7. Exact URL-joining logic in the SDK (trailing-slash handling in `base_url`). I verified the default and the README example only, not the join code.
8. Whether `platform.openai.com/docs/api-reference/chat/create` (the human-readable reference) differs from the OpenAPI file. Blocked by 403; not checked. The spec says it is generated from OpenAI's upstream source [S1].

## 6b. Resolved by testing in step 4.7
On 2026-10-19 the `openai` Python SDK 2.48.0 was pointed at the gateway (local stub upstream):
- Unknown 2 (SDK behaviour on error bodies): gateway errors in the OpenAI shape were raised as typed `APIStatusError` / `AuthenticationError` with the gateway's `code` and `message` intact.
- Unknown 7 (URL joining): `base_url="http://host:port/v1"` (no trailing slash) reached `POST /v1/chat/completions`.
- A custom `X-API-Key` header set through `default_headers` reached the gateway, which settles the auth recommendation in section 5 for the Python SDK.
Still untested: the Node SDK, any real OpenAI/Claude/Gemini endpoint, and unknowns 1, 3, 4, 5, 6 and 8.

## 7. Anthropic and Gemini (step 4.0b)
Why: the owner uses Claude and Gemini, so an OpenAI-only proxy would not serve the actual use case. Same method as above: vendor docs plus Google's machine-readable discovery document [S9]. No live calls were made (no API keys), so everything below is from documentation, not tested behaviour.

### 7.1 Route A: the vendors' OpenAI-compatible endpoints
| Item | Anthropic [S5] | Gemini [S6] |
|---|---|---|
| Base URL | `https://api.anthropic.com/v1/` | `https://generativelanguage.googleapis.com/v1beta/openai/` |
| Auth | OpenAI SDK with a Claude API key; `authorization` listed as fully supported. Keys with access to several workspaces also need an `anthropic-workspace-id` header. | Gemini API key passed as the SDK `api_key`. Header form not stated on the page I read. |
| Vendor's own stability statement | "primarily intended to test and compare model capabilities, and is not considered a long-term or production-ready solution for most use cases" | "Support for the OpenAI libraries is still in beta" |
| Chat completions, streaming, tools | Supported, with the exceptions below | Supported (also structured outputs, embeddings) |
| Notable gaps | `n` must be 1; system/developer messages are hoisted into one `system` string; `response_format`, `metadata`, `user`, `prediction`, `logit_bias`, `store` and others are silently ignored; audio and `file` parts are ignored (stripped); `name` ignored; image URLs supported; responses always have one choice | Vendor-specific features (cached content, thinking config, safety settings, grounding) go through `extra_body` |
| Errors | "consistent error formats with the OpenAI API", messages not equivalent | Not stated on the page I read |
| Last updated | Not shown | 2026-10-14 |

**Finding that changes 4.2:** both vendors tell users to send vendor-specific options as extra top-level body fields (`extra_body` in the Python SDK; for Claude, `thinking`). A strict request model that rejects unknown fields would break those features. A model that forwards unknown fields would send unscanned content upstream. Step 4.1 must choose, per field, which side to fail on. Interpretation: an allow-list of known-safe extra keys per upstream is the fail-closed option.

### 7.2 Route B: the native formats
| Item | Anthropic Messages [S7], [S8] | Gemini generateContent [S9], [S10] |
|---|---|---|
| Endpoint | `POST https://api.anthropic.com/v1/messages` | `POST https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent`; streaming is a separate method, `:streamGenerateContent`. The model is in the URL, not the body. |
| Auth | `x-api-key` header plus `anthropic-version` header (the docs' curl example uses `2023-06-01`) | `x-goog-api-key` header in the current docs [S11]; the discovery doc also lists a `key` query parameter [S9] |
| Required body | `model`, `max_tokens`, `messages` | `contents` |
| System prompt | top-level `system`: string or list of text blocks | top-level `systemInstruction` (a Content object) |
| Turns | `messages[]`, roles `user` and `assistant` only; `content` is a string or a list of typed blocks | `contents[]`, roles `user` and `model`; each has `parts[]` |
| Block / part types | `text`, `image`, `document`, `tool_use`, `tool_result`, `thinking` and others | `text`, `inlineData`, `fileData`, `functionCall`, `functionResponse`, `executableCode`, `codeExecutionResult`, `toolCall`, `toolResponse`, `audioTranscription` and others (discovery `Part`) |
| Text outside the main prompt | `document` blocks (`source` of type text, `title`, `context`); `tool_use` input; `tool_result` content; `metadata.user_id` | `functionCall.args`, `functionResponse.response`, `labels`, `cachedContent` reference |
| Response | `type: "message"`, `content[]` blocks, `stop_reason`, `usage` | `candidates[].content.parts[]`, `promptFeedback`, `usageMetadata` |
| Error body | `{"type":"error","error":{"type","message"},"request_id"}`; statuses include 402, 413, 504, 529; `request-id` response header [S8] | Discovery shows a `Status` object (integer `code`, `message`, `details`) [S9]; the Gemini errors page shows `{"error":{"code":"invalid_request","message":...}}` with string codes and also 504 and 416 [S12]. These two disagree (see Unknowns). |

### 7.3 What the three formats share (basis for the seam)
Interpretation, from the tables above: every format reduces to "some text strings, each belonging to a role, inside a nested structure the provider defines". Redaction only needs the strings. So the neutral core function can be `redact_texts(list[str]) -> (list[str], entity_counts)`, with each format's adapter in `api/` walking its own structure (Anthropic blocks, Gemini parts, OpenAI messages), calling that function, and writing results back in place. This is slightly more neutral than the plan's `redact_messages(messages, ...)` and keeps `core/` free of any provider vocabulary. Each adapter then owns its schema, its list of scanned fields, and its reject list.

### 7.4 Options and recommendation
| | A. Compatibility endpoints only | B. Add native adapters |
|---|---|---|
| Extra gateway code | None beyond the OpenAI route | One schema + walker per provider; my estimate is on the order of 100 lines each, unmeasured |
| Works for the owner's Claude/Gemini use | Yes, within the gaps in 7.1 | Yes, full native features |
| Vendor support status | Anthropic: not for production; Gemini: beta | Supported primary APIs |
| Risk to redaction | Ignored fields and hoisting are silent (e.g. a system message moves position) but the text is still scanned before forwarding | New code paths to test; Claude and Gemini content types to reject or scan |
| Fits plan size | Yes | Better as its own step or phase |

Recommendation: finish the OpenAI route (4.1 to 4.7), document Route A for Claude and Gemini with the gaps, and treat native Anthropic (then Gemini) as Phase 5 using `redact_texts`. Reason: zero extra code now, the personal use case is covered, and a second adapter is the second real use that justifies an abstraction. Switch Anthropic to native sooner if the compatibility gaps (n=1, ignored `response_format`, no prompt caching) hurt in practice.

### 7.5 Requirements (additions)
| Rule (source + section) | Plain meaning | Applies? | Feature or test it implies | Priority | Confidence |
|---|---|---|---|---|---|
| [S5] "Getting started", base URL | Claude is reachable by OpenAI SDKs at `https://api.anthropic.com/v1/` | Yes | Document as an upstream value of `LLM_UPSTREAM_BASE_URL`; do one manual run before claiming it | High | Medium (docs only, untested) |
| [S6] base URL | Gemini is reachable at `.../v1beta/openai/` | Yes | Same as above | High | Medium |
| [S5] "Important OpenAI compatibility limitations" | Several fields are ignored or reshaped silently | Yes | README limits list; do not promise feature parity | High | High |
| [S5], [S6] extra body fields | Vendor options travel as extra top-level fields | Yes | 4.1 decision on unknown fields; test that an unknown field is handled per that decision | High | Medium |
| [S5] stability note, [S6] beta note | Vendors do not call these layers production-grade | Yes | README wording: "convenience route, vendor-labelled testing/beta" | Medium | High |
| [S7] `system`, content blocks | Claude native format hides text in `system` and blocks | Later | Phase 5 walker and tests per block type | Medium | High |
| [S9] `systemInstruction`, `Part` | Gemini native format hides text in `systemInstruction` and parts | Later | Phase 5 walker | Medium | High |

### 7.6 New unknowns
1. Does the Gemini compatibility endpoint accept `Authorization: Bearer <key>` (what OpenAI SDKs send) or only its own header? The page says to pass the key as `api_key`, which implies the SDK's Bearer header, but I did not see it stated. A one-request test with the owner's key would settle it.
2. Which Gemini error shape is current: integer-code `Status` [S9] or string-code [S12]? The fetched errors page may describe a newer API than `generateContent`. Check against a real error response.
3. Does the Anthropic compatibility layer accept every OpenAI-style field the gateway might forward, or return 400 for some? The doc says most unsupported fields are ignored, but also names 400 errors for some `temperature`/`top_p` values on newer models.
4. Gemini compatibility endpoint: exact list of ignored fields and the exact error body. Not on the page I read.
5. Anthropic `anthropic-version` header: I only saw the value in a curl example. Confirm in the versioning page before a native adapter.
6. Should the gateway add the vendor workspace header (`anthropic-workspace-id`) as a forwarded header? Depends on whether the owner's key spans workspaces.

## 8. Sources
| # | Title | Publisher | URL | Date | Accessed |
|---|---|---|---|---|---|
| S1 | `openapi.json` (OpenAPI 3.1, info.version 2.3.0), repo `openai/openai-openapi`, MIT | OpenAI (vendor, primary) | https://github.com/openai/openai-openapi (file: `openapi.json`, `master`) | last commit 2026-10-18 (sha f88d2f7) | 2026-10-19 |
| S2 | `openai-python` README | OpenAI (vendor, primary) | https://github.com/openai/openai-python | `main` at access time | 2026-10-19 |
| S3 | `openai-python` `src/openai/_client.py` | OpenAI (vendor, primary source code) | https://github.com/openai/openai-python/blob/main/src/openai/_client.py | last commit to file 2026-10-06 | 2026-10-19 |
| S4 | Error codes guide | OpenAI (vendor, primary) | https://developers.openai.com/api/docs/guides/error-codes (301 from `platform.openai.com/docs/guides/error-codes`) | not shown | 2026-10-19 |

| S5 | OpenAI SDK compatibility (Anthropic) | Anthropic (vendor, primary) | https://platform.claude.com/docs/en/api/openai-sdk (redirects to `/cli-sdks-libraries/libraries/openai-sdk`) | not shown | 2026-10-19 |
| S6 | Gemini API OpenAI compatibility | Google (vendor, primary) | https://ai.google.dev/gemini-api/docs/openai | 2026-10-14 (as shown on page) | 2026-10-19 |
| S7 | Messages API reference | Anthropic (vendor, primary) | https://platform.claude.com/docs/en/api/messages | not shown | 2026-10-19 |
| S8 | Claude API errors | Anthropic (vendor, primary) | https://platform.claude.com/docs/en/api/errors | not shown | 2026-10-19 |
| S9 | Generative Language API discovery document, `v1beta`, revision 20261017 | Google (vendor, primary, machine-readable) | https://generativelanguage.googleapis.com/$discovery/rest?version=v1beta | revision 2026-10-17 | 2026-10-19 |
| S10 | Gemini `generateContent` reference | Google (vendor, primary) | https://ai.google.dev/api/generate-content | not shown | 2026-10-19 |
| S11 | Using Gemini API keys | Google (vendor, primary) | https://ai.google.dev/gemini-api/docs/api-key | not shown | 2026-10-19 |
| S12 | Gemini API errors | Google (vendor, primary) | https://ai.google.dev/gemini-api/docs/api-errors | not shown | 2026-10-19 |

Method note for S5 to S12: pages S6, S7, S10, S11 and S12 were read through a page summariser, which also truncated S7 and S10 (only the first 100,000 characters of each were read). Treat field lists from those as likely-complete for the first-level request shape, not exhaustive. S5 and S8 were read in full; S9 was parsed directly.

Not retrievable: `platform.openai.com/docs/api-reference/chat/create` and `/authentication` (HTTP 403 to scripted requests; not bypassed). `docs/api-reference` on `developers.openai.com` returned 404 for the path I guessed.
