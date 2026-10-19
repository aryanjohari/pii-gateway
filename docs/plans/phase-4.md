# Plan: Phase 4, LLM proxy (non-streaming first)

Goal: a drop-in, OpenAI-compatible `POST /v1/chat/completions` that redacts message text with the existing engine (including the NZ pack), forwards the cleaned request to an upstream LLM, and returns the reply. A developer changes one base URL and their prompts are scrubbed.
Size: medium-large (about 1.5 to 2 weeks, ~400 changed lines). Branch: `phase-4-proxy`. One commit per step; stop for approval after each. Streaming is a separate, optional step (4.8) and ships only if time allows.
Audience: developers (you included). Not a compliance product and not a non-technical tool; say so in the README. Worked example the design must satisfy: a clinic's internal tool sends notes containing a name, an NHI and a phone number; the upstream model sees only placeholders (`<PERSON>`, `<NZ_NHI>`, `<PHONE_NUMBER>`).

## Design decisions (state these in an ADR)
- **Redact only, no restoration (v1).** The reply keeps placeholders. Restoring originals needs a token map held in memory, which creates a new place for PII to leak and a lifetime problem. Record it as a possible later phase.
- **One wire format first:** OpenAI chat-completions request and response shape. Claude and Gemini are reachable through their vendors' OpenAI-compatible endpoints by setting `LLM_UPSTREAM_BASE_URL` (see `docs/research/llm-api-formats.md` section 7). Document them as a convenience route with the vendors' stated limits (Anthropic: testing aid, not production; Gemini: beta), and do not claim feature parity or native Anthropic/Gemini support. Native adapters are Phase 5.
- **Format-neutral core:** `core/` exposes `redact_texts(texts: list[str])` returning cleaned strings and entity counts, with no provider vocabulary. The OpenAI adapter in `api/` walks messages, calls it, and writes results back. A later native adapter adds only its own schema and walker.
- **Unknown request fields:** vendors send options as extra top-level fields (`extra_body`, Claude `thinking`). Decide in 4.1 per field: scan, reject, or pass through on a small allow-list per upstream. Default is fail closed (reject unknown fields that could carry text).
- **Scope of redaction:** string `content` of messages, and text parts of list-form `content`. Images, audio, tool calls, function arguments and `name` fields are **not** scanned in v1. Requests containing them are either passed through with a warning header or rejected; decide in 4.1 (recommendation: reject with a clear 422 so nothing unscanned is forwarded silently, matching the repo's fail-closed stance).
- **Upstream key comes from the caller,** passed in `Authorization` and forwarded; never logged, never stored. Gateway auth stays on `X-API-Key` (existing `verify_http_auth` pattern). Upstream base URL comes from an env setting.
- **Reuse the existing engine.** Call `sanitize_free_text` through the already-built analyzer in app state; do not build a second analyzer or add a second redaction path.
- **No raw content in logs.** Log message counts, entity-type counts, upstream status and duration only, per the repo's security rules.
- **Fail closed:** if redaction raises, return 500 and do not forward anything.
- **Bounded:** reuse the existing body-size and character limits and the rate limit; add an upstream timeout setting.

## Steps

| Step | Change | Done when |
|---|---|---|
| 4.0 | `/domain-research` (primary docs only) on the OpenAI chat-completions request/response schema and error format, and the exact `base_url` convention clients use. Save to `docs/research/llm-api-formats.md`. Unknowns listed, nothing guessed. | research reviewed by you |
| 4.0b | Done. Research extended to Anthropic Messages, Gemini generateContent and both compatibility endpoints (section 7 of the research doc). | research reviewed by you |
| 4.1 | Learning note + ADR: redact-only, OpenAI format first, Claude/Gemini via compatibility endpoints, native adapters deferred, what is and is not scanned (including `name`, `prediction`, tool definitions, `user`), reject-vs-pass-through for unsupported content and unknown fields, `stream: true` rejected until 4.8, auth header choice. | ADR in your own words |
| 4.2 | Pydantic request/response models for the supported subset of the chat schema (`api/schemas`). Unsupported content types give a 422 with a code. | unit tests: valid request, list-form content, image part rejected, empty `messages` rejected |
| 4.3 | Pure function `redact_texts(texts, ...)` in `core/` returning cleaned strings and entity counts; no I/O, no logging. The OpenAI message walker (string content, list-form text parts, roles preserved) lives in `api/` and is tested there. | unit tests: empty string untouched, order preserved, counts correct; walker tests: string content, list-form text parts, roles preserved; core coverage stays 100% |
| 4.4 | Route `POST /v1/chat/completions`: auth, limits, redact, forward, return. Upstream client created once in the lifespan and closed on shutdown. **Needs your approval: `httpx` is currently a dev-only dependency and would move to runtime dependencies. No other new dependency.** | integration tests with a fake upstream (ASGI app or `httpx.MockTransport`): upstream receives only placeholders; caller's key reaches upstream and is absent from logs and artifacts |
| 4.5 | Failure paths: upstream timeout → 504, upstream 4xx/5xx → passed through with a gateway error code, redaction failure → 500 and **nothing forwarded** (assert the fake upstream got zero calls). Settings: `LLM_UPSTREAM_BASE_URL`, `LLM_UPSTREAM_TIMEOUT_SECONDS`; update `.env.example`. | tests for each path; error messages carry context (which upstream, status), never message text |
| 4.6 | NZ worked example as an integration test: clinic note with name, NHI and phone under `config.nz.yaml`; assert placeholders reach upstream. Add one eval-style negative (look-alike number is not over-redacted). | test passes; the README example was actually run, not written by hand |
| 4.6b | Manual run, not a test: one request through the gateway to Claude and one to Gemini via their compatibility endpoints using your own keys. Record the result and any error body in the research doc (settles its section 7.6 unknowns 1 and 2). Keys stay in the shell environment only. | result recorded, or skipped and stated |
| 4.7 | Docs: README section ("use it with the OpenAI SDK by changing `base_url`"), limits (not scanned: images, tools; Claude and Gemini via compatibility endpoints with the vendors' listed gaps; multi-turn history is redacted per message but a miss is still a miss; reply keeps placeholders), `docs/ARCHITECTURE.md` update, C4 note. Wording: "helps reduce exposure", never "compliant" or "anonymised". | docs match the code; links valid |
| 4.8 | **Optional.** Streaming (SSE) pass-through of the upstream response. Request redaction is unchanged, so only the response path streams. Skip if 4.1 to 4.7 took longer than planned and record it as a README limit. | test with a fake streaming upstream; client disconnect closes the upstream request |

## Honest-reporting rules
- Add a latency line to the README: p50/p95 added by the gateway, measured with the fake upstream, so the cost is known.
- State plainly that a missed entity reaches the LLM. Link the Phase 2 and 3 precision/recall tables next to the proxy section.
- Do not describe the proxy as protecting browser use of chat websites; it only covers code that calls an API.

## Out of scope
Restoring originals in replies, native Anthropic and Gemini formats (Phase 5), tool/function-call and image scanning, per-user keys or quotas, browser extension, hosted multi-tenant service, CLI, rate-limit proxy-IP fix, pre-commit, dependency lockfile.

## Questions to settle before 4.2
- Reject or pass through unsupported content types? (Recommendation: reject, 422.)
- Should upstream base URL be fixed per deployment (env) or allowed per request? (Recommendation: env only. A per-request URL lets a caller point the gateway at any host, which is an SSRF risk.)
- Does `X-API-Key` for the gateway conflict with SDKs that only let you set `Authorization`? Research answer: the Python SDK accepts custom headers, so keeping `X-API-Key` works for developers who control their client; it fails for tools with a single key field. Recommendation: keep `X-API-Key`. Confirm in 4.1.
- Forward `OpenAI-Organization` / `OpenAI-Project` / `anthropic-workspace-id` upstream? (Recommendation: forward only `Authorization` in v1; list the rest as a limit.)
- Unknown request fields: reject, or allow-list per upstream? (Recommendation: reject by default.)

## Skills
`/domain-research` at 4.0, `claude-api` skill for the native Anthropic adapter in Phase 5, `/test-gap` after 4.5, `/security-review` and `/scope-check` before the PR, `/phase-close` at the end.

## Learning checkpoint (`docs/LEARNING.md`)
In your own words: why redact-only is safer than restore, what "fail closed" means for a proxy, why the upstream URL must not come from the request (SSRF), and what the gateway can and cannot see.
