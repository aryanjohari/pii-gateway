# Plan: Phase 0 (packaging and cleanup) and Phase 1 (batch hardening)

Goal: make the repo credible as a flagship before adding features. One concern per branch/PR. Wait for approval between steps.
Baseline (2026-10-19): 52 tests pass, ruff and mypy clean, coverage 71%. Weakest: `connectors/s3_inbox.py` 6%, `jobs/scheduler.py` 32%, `jobs/postgres_batch_job.py` 40%, `storage/s3_compatible_backend.py` 37%, `jobs/file_ingest.py` 49%.

## Phase 0: cleanup and first release (branch `phase-0-cleanup`)
Each step is its own commit.

| Step | Change | Done when |
|---|---|---|
| 0.1 | Ask first: move `resume.md`, `.cursorrules`, `architecture.plan.md` and `docs/archive/` out of the repo root (keep locally, untrack). Do not delete. | root lists only product files; no broken links (`grep` for old paths) |
| 0.2 | README top: replace "Visitor overview: see portfolio.yaml" with a one-line pitch, demo link, and a before/after redaction example | pitch visible without scrolling; example output was run, not written by hand |
| 0.3 | Add a README "Limitations" section (best-effort NLP, not a compliance product, wording from `docs/research/nz-privacy-compliance.md`) | no use of "compliant" or "anonymised" |
| 0.4 | Tag `v0.1.0` and confirm the GHCR publish workflow runs | needs explicit approval: pushing a tag publishes an image |

Skills: `/scope-check` before each commit, `/repo-audit` at the end.

## Phase 1: batch hardening (branch `phase-1-batch`)
Fix tests first, then robustness. No new features.

| Step | Change | Tests (fail without the change) |
|---|---|---|
| 1.1 | Tests for `file_ingest`: happy path (CSV, JSON array), bad file (failure path), already-processed file skipped (idempotence) | 3 integration-style tests using a temp inbox dir |
| 1.2 | Tests for `postgres_batch_job` using the `aiosqlite` dev dependency already in the repo, plus cursor advancing | happy path and "no rows" |
| 1.3 | Tests for `s3_inbox` and `s3_compatible_backend` by faking the aioboto3 client at the boundary (no new dependency such as `moto` without approval) | list, download, upload, error propagated with context |
| 1.4 | Timeouts: botocore `Config(connect_timeout, read_timeout)` for S3; asyncpg `command_timeout` for Postgres. Values come from settings with defaults. | test that a timeout error is raised with context (what, which key/query) |
| 1.5 | Raise the coverage floor from 0 to a real number (current coverage after 1.1–1.4, minus 2 points) | CI fails if it drops |

Open questions to settle before 1.4:
- Where do settings for timeouts live (`settings.py`)? Check the existing pattern.
- `write_sanitized_rows_ndjson` takes a list, so large exports sit in memory. Note this in the docs now; fixing it is out of scope for this phase.

Skills: `/test-gap` after 1.3, `/code-review` and `/scope-check` before the PR.

## Out of scope
Evaluation harness, NZ recognisers, LLM proxy, rate-limit proxy-IP fix, pre-commit, dependency lockfile. These are later phases.

## Learning checkpoint (write in `docs/LEARNING.md`)
After each phase, in your own words: what each test proves, why timeouts matter for a service, and what "idempotent" means for the file inbox.
