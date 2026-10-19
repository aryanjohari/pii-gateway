# Plan: Phase 6, a demo that explains itself

Goal: fix the issues found by the frontend audit, then rebuild the `web/` playground around one job: show a visitor in 30 seconds that it redacts personal data from text before an AI sees it. No gateway features.
Size: medium to large. Branch: `phase-6-web-demo`. One commit per step; stop for approval after each.
Source: `/frontend-audit` run on 2026-10-20. Overall grade C (capped: no accessibility testing at all, textarea focus fails, results not announced, critical `next` advisory). Runtime checks (axe, Lighthouse, 375px) were UNKNOWN because no browser was available.

## Steps

| Step | Change | Done when |
|---|---|---|
| 6.0 | This plan. | file committed |
| 6.1 | **Audit quick wins, no new dependencies:** `npm audit fix`; live region (`role="status"`) and `role="alert"` for errors on the output; visible focus ring and input boundary on the textarea; `aria-pressed` on the mode toggle; skip link; clearer sample chip names. | `npm run typecheck` and `npm run build` pass; `npm audit --omit=dev` has no critical entry; each change cited to its audit item |
| 6.2 | **`web/DESIGN.md`**, one page: the user, three screens (playground, "what happened", self-host), tone, and a table of states with message and next step. | file reviewed and approved |
| 6.2b | **Playground policy with the NZ entities** (added after 6.2, owner-approved). The public demo policy redacted only email, person and phone, and `config.nz.yaml` lacks `PERSON` and `EMAIL_ADDRESS`, so a new `config/examples/config.demo-nz.yaml` carries all six; compose overlay and docs repointed; one integration test. `config.demo.yaml` is unchanged so the README evaluation table stays valid. | the three NZ presets redact under this policy (test); full suite green |
| 6.3 | **Redesign the playground** as one before/after panel ("your text" and "the prompt the AI would see", both labelled, `<TYPE>` labels in text). Split into commits: (a) move state and fetch into a `useSanitize` function; (b) before/after panel; (c) NZ presets (clinic note with NHI, invoice with IRD number, email with driver licence); (d) every state: empty, too long, rate limited, offline, invalid JSON; (e) honesty notices and limits note linking to the README evaluation section. | each state reachable and shown in `DESIGN.md`; no "compliant" or "anonymised" in `web/` (`grep`) |
| 6.4 | **Tooling and tests:** ESLint with `jsx-a11y` and a working `npm run lint`; component tests by role; 2 to 3 Playwright flows (happy path, error path, keyboard-only) with an axe check; add lint, tests, the browser flows and `npm audit --omit=dev --audit-level=high` to `web.yml`. | CI green; a deliberate a11y regression fails it on a throwaway branch |

## Decisions and limits
- The demo calls `/v1/sanitize`, not the LLM chat proxy. The "what the AI sees" panel says "this is the prompt that would be sent"; it must not imply a live LLM call.
- Highlighting removed text on the left needs offsets. Check what `/v1/sanitize` returns before 6.3b. If it only has entity counts, derive the highlight from the placeholders in the redacted text. Changing the API needs separate approval.
- The client limit for "too long" must match `sanitize_max_chars` (10000) in `src/pii_gateway/settings.py`. Read it, do not duplicate it silently.
- Eval numbers are linked from the README evaluation section, not copied into the UI, so the page cannot drift. The caveat (synthetic data, written by the recogniser author) sits next to the link.
- Wording: "redacts personal data (best effort)". Never "anonymised" or "compliant".
- Response validation: a small hand-written type guard, no `zod` unless approved.

## New dependencies (each group needs approval at the step that uses it)
- 6.4: `eslint`, `eslint-config-next`, `eslint-plugin-jsx-a11y`.
- 6.4: `vitest`, `@testing-library/react`, `@testing-library/user-event`, `jsdom`.
- 6.4: `@playwright/test`, `@axe-core/playwright`.

## Out of scope
New recognisers, gateway API changes, streaming, restoring originals, hosting changes, the API route's rate-limit and proxy-header behaviour (noted below).

## Noticed in the audit, not planned
- `web/app/api/sanitize/route.ts` trusts the first `x-forwarded-for` value for its rate limit, and its in-memory counter is per serverless instance.
- The same route relays the upstream payload and status as-is.
- `web.yml` has no `npm audit` step.

## Manual checks after 6.4
Screen reader pass (VoiceOver), keyboard-only run, 200% zoom, a real phone, forced-colors mode, Lighthouse.
