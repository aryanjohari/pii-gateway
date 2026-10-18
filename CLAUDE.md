# PII Gateway: repo rules for Claude

Overrides `~/.claude/CLAUDE.md` where they conflict. Product overview: `PROJECT.md`. Design: `docs/ARCHITECTURE.md`. Current work plan: `docs/plans/phase-0-1.md`.

## Commands
- Install: `pip install -e ".[dev]"` then `python -m spacy download en_core_web_sm`
- Test: `pytest` (coverage is printed; the floor is set in `pyproject.toml`)
- Lint: `ruff check src tests`
- Types: `mypy src` (strict)
- CI runs all four plus `docker build .`. All must pass before a task is done.

## Layout
- `src/pii_gateway/core/`: pure redaction logic. Must not import `api`, `connectors`, `jobs` or `storage`, and must not log.
- `api/`: FastAPI routes, auth, rate limit, request limits.
- `jobs/`, `connectors/`, `storage/`: batch and file ingestion, Postgres/S3/CSV/JSON I/O, artifact backends.
- `tests/unit` for pure logic, `tests/integration` for HTTP and job flows.

## Code rules
- Functional style. No classes unless a library requires them (Pydantic models and settings are fine).
- Strict type hints on all parameters and returns. Pydantic v2 models for request/response schemas, no raw dicts for validation.
- `async def` for I/O (HTTP, DB, object storage). Use `aioboto3` for S3.
- Guard clauses over nested `if`. API errors use `HTTPException` with clear codes.
- Presidio `AnalyzerEngine` is built once per process in the FastAPI lifespan. Never per request.
- 12-factor: config from environment (`settings.py`, `.env.example` is the committed example), logs to stdout, processes stateless. Storage is local disk or an S3-compatible endpoint; never assume AWS-only.
- `snake_case` names.

## Security rules (non-negotiable)
- Never log raw request bodies, SQL row payloads, file contents, or any text that may contain PII. Exceptions and log lines carry identifiers (job name, key, file name), not data.
- Batch SQL must be reviewed, parameterized and read-only.
- Do not claim the product is "compliant" or that output is "anonymised". It is best-effort redaction.

## Testing rules
- Every redaction logic path has unit tests (target 100% for `core/`).
- Mock only at true boundaries (network, S3 client, clock). Do not mock the repo's own code.
- No new test dependency (for example `moto`) without asking. `aiosqlite` is already available for DB tests.

## Git and scope
- Branch per phase (`phase-0-cleanup`, `phase-1-batch`), one commit per plan step, commit messages say why.
- Never tag, push, or trigger the publish workflow (`v*` tags publish an image to GHCR) without explicit approval for that action.
- Never rewrite git history without explicit approval.
- Local-only files (untracked, kept on disk, listed in `.gitignore`): `resume.md`, `.cursorrules`, `architecture.plan.md`, `docs/archive/`. Treat as read-only unless asked.
- Out of scope until planned: evaluation harness, NZ recognisers, LLM proxy, rate-limit proxy-IP fix, pre-commit, dependency lockfile.
