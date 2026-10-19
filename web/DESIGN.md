# Demo design

**One job:** show a visitor, in 30 seconds, that PII Gateway redacts personal data from text before an AI sees it.

**Who it is for:** a developer or small-business owner deciding whether to try it. They have not read the README. They will paste something, look at the result, and either self-host or leave.

**Tone:** plain and honest. Say "redacts (best effort)". Never "compliant", "anonymised", "secure" or "guaranteed". Say what it misses. No marketing adjectives.

## Three screens

All three are sections of one page (`/`), so there is no routing to build.

### (a) Playground
- One text box, three NZ presets (clinic note with an NHI, invoice with an IRD number, email with a driver licence) and a JSON mode.
- A visible notice next to the box: **sample data only, do not paste real information.**
- One primary button: "Redact".
- Presets fill the box and do not submit, so the visitor sees what is about to be sent.

### (b) What happened
Appears below the box after a request. One story, two labelled panels side by side (stacked at 375px):

| Left: "Your text" | Right: "What the AI would see" |
|---|---|
| The original, with each detected item marked and labelled in text, e.g. `[NZ_NHI]`, not by colour alone | The redacted prompt with `<NZ_NHI>`, `<PERSON>` placeholders |

- Under the panels: entity counts by type, and the time taken.
- The right panel is the prompt that **would** be sent. The demo calls `/v1/sanitize`; it does not call an LLM, and the page must not imply it does.
- A short **limits note**: names in free text may be missed (for example some Māori names), a mistyped NHI or IRD number is not redacted, and licence numbers match by shape only. It links to the README evaluation section, with the caveat that the numbers come from synthetic data written by the same author as the detectors.

### (c) Self-host
- The `docker compose` commands, a link to the repo, and one sentence on why: the public demo is rate limited and should never receive real data.

## States

Every state has a message and a next step. Messages are text in a live region (`role="status"`); none relies on colour alone.

| State | Message | Next step offered |
|---|---|---|
| Idle | "Pick a sample or paste text, then press Redact." | Presets |
| Empty input | "Add some text first, or pick a sample above." Button stays enabled so the message can be read. Focus moves to the box. | Presets |
| Too long | "That is N characters; the demo accepts up to 10,000." (client check for text; the gateway's 413 for JSON) | Shorten, or self-host link |
| Invalid JSON | "That is not valid JSON." or, for a list or single value, "The JSON must be an object…". Field linked with `aria-describedby`; focus returns to it. | Fix, or use a preset |
| Loading | "Redacting…" | none |
| Rate limited (429) | "Too many requests from this address. Wait a minute and try again, or self-host." | Wait, or self-host link |
| Offline (503, Pi down) | "The public demo is offline. This does not affect self-hosted copies." | Self-host link |
| Unexpected error | "Something went wrong. Try again in a moment." Our own wording; upstream error bodies are never shown. | Press Redact again |
| Success | Both panels plus counts. | Try another preset, or self-host |

The 10,000 limit is `sanitize_max_chars` in `src/pii_gateway/settings.py`. The page keeps it in one constant (`web/lib/limits.ts`); the gateway stays the source of truth and answers 413.

## Accessibility baseline (WCAG 2.2 AA)
Labelled inputs, results announced, keyboard-only use, visible focus (3:1), text contrast 4.5:1, 24px minimum targets, no horizontal scroll at 375px or 200% zoom, `prefers-reduced-motion` respected.

## Open questions, to settle before step 6.3
1. **The public demo policy does not redact NZ identifiers, and `config.nz.yaml` is not a drop-in replacement.** `config/examples/config.demo.yaml` lists only `EMAIL_ADDRESS`, `PERSON` and `PHONE_NUMBER`. `config.nz.yaml` lists only `NZ_NHI`, `NZ_IRD`, `NZ_DRIVER_LICENCE` and `PHONE_NUMBER`, so switching to it would stop redacting names and emails. Resolved (owner, 2026-10-20): a new file, `config/examples/config.demo-nz.yaml`, with all six entities. `config.demo.yaml` is unchanged so the README evaluation table stays valid. The Pi is not touched by this repo's changes.
2. **Highlighting the left panel needs offsets.** Checked: `/v1/sanitize` returns `entity_summary` (counts per type) and `duration_ms` only, no offsets. The markers are therefore derived from the placeholders in the redacted text. Changing the API needs separate approval.
