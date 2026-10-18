# ADR 0002: Batch SQL comes only from the policy file, selected by name

- Status: Accepted (recorded retroactively on 2026-10-19)

## Context
The Postgres batch job exports rows, sanitizes them and writes an artifact. Anything that lets a caller choose SQL turns the gateway into a database proxy that reads data it should never hand out.

## Decision
- SQL lives in the mounted policy file under `postgres_batch.queries`, each entry validated by `BatchQueryDef` (`policy_schema.py`) at startup.
- The job runs `queries[query_name]` where `query_name` is also in the policy (`postgres_batch_job.py`). The HTTP trigger `/internal/jobs/postgres-batch` takes no SQL or query name from the caller.
- Execution uses SQLAlchemy `text()` with bound parameters. The only parameter today is `:since`, filled from the saved cursor (`params_from: last_run_cursor`).
- Credentials stay in the environment (`POSTGRES_BATCH_DSN`), never in the policy file.

## Consequences
- Queries are reviewable as a file in version control, and a request cannot change what runs.
- **Read-only is not enforced by the code.** The policy author controls the SQL, so use a database role that can only `SELECT`. The README and architecture notes already say this.
- A missing `query_name` logs an error and skips the run rather than guessing.
- The cursor is the wall-clock time after the query finishes, so a row changed while the query runs can be missed. Known limit, not solved here.

## Alternatives considered
- **Accept SQL in the request:** rejected, it removes the security boundary.
- **A query builder or ORM models:** rejected as more code than a small export feature needs.
