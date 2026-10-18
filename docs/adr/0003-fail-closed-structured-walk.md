# ADR 0003: Structured JSON is sanitized fail-closed

- Status: Accepted (recorded retroactively on 2026-10-19)

## Context
Callers send nested JSON. Field names that carry personal data are known for some schemas and unknown for others. If only declared fields were redacted, any new or misspelled field would leak silently.

## Decision
`sanitize_structured_value` (`core/sanitize_structured.py`) walks every dict and list recursively:
- A string field with a declared rule (`redact`, `tokenize`, `mask`) gets that deterministic treatment.
- A field declared `passthrough` still runs through Presidio, so "passthrough" means "no field rule", not "leave alone".
- Every undeclared string runs through Presidio with the policy's entity list.
- There is no setting that skips scanning for a string.

## Consequences
- New fields are scanned by default, which is the safe failure direction.
- Cost: more NLP calls, and `sanitize_payload` analyzes strings twice (once for counts, once to redact). Noted as an inefficiency in `docs/ARCHITECTURE.md`.
- NLP is best-effort, so undeclared fields can still be missed. Declare known sensitive fields to get deterministic redaction.
- Not covered: non-string values (numbers, booleans) are returned unchanged, and dictionary keys are not scanned. A phone number stored as an integer would pass through.
- `tokenize` is a label like `<EMAIL_ADDRESS>`, not a reversible or cryptographic token.

## Alternatives considered
- **Redact only declared fields:** rejected, silent leaks on any schema change.
- **Drop all undeclared fields:** rejected, it destroys data the caller may legitimately need.
