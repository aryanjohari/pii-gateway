# C3 — Components: `pii-gateway`

Zoom of the single FastAPI / Uvicorn process (`Dockerfile` CMD). All components share one Docker image and one OS process.

| ID | Code area | Role |
|----|-----------|------|
| Sanitize API | `api/routes_sanitize.py`, `api/schemas.py` | `POST /v1/sanitize` |
| Internal jobs API | `api/routes_internal.py` | `POST /internal/jobs/postgres-batch`, `POST /internal/jobs/file-ingest` |
| Healthz | `main.py` | `GET /healthz` |
| Correlation middleware | `api/middleware.py` | `X-Correlation-ID` (only Starlette middleware besides optional CORS) |
| API key auth | `api/auth.py` | Route helpers — **not** middleware; constant-time key compare |
| Settings | `settings.py` | Env-only secrets/DSNs/storage/scheduler flags |
| Policy loader | `config_loader.py`, `policy_schema.py` | Mounted policy at lifespan start |
| Sanitize pipeline | `core/sanitize_pipeline.py`, `sanitize_text.py`, `sanitize_structured.py`, `entity_summary.py` | Text + recursive structured redaction |
| Presidio engines | lifespan in `main.py` | `AnalyzerEngine` / `AnonymizerEngine` once per process |
| Connectors | `connectors/` | Postgres stream, CSV (Pandas), JSON array, S3 inbox |
| Jobs + scheduler | `jobs/postgres_batch_job.py`, `file_ingest.py`, `batch_common.py`, `scheduler.py` | Batch runners; optional `AsyncIOScheduler` |
| Storage + state | `storage/`, `state_store.py`, `storage/paths.py` | Outbound local/S3; Postgres cursor + processed-file index |
| Structured logging | `logging_config.py` | Stdout; no raw bodies from core sanitize modules |

## Distinctive design (do not flatten away)

1. **Fail-closed structured walk** — Declared fields use `redact` / `tokenize` / `mask` / `passthrough`; undeclared strings and `passthrough` still go through Presidio (`sanitize_structured.py`).
2. **Named SQL boundary** — Batch SQL text lives only in the policy file; HTTP picks `query_name`, never supplies SQL (`batch_postgres_sqlalchemy.py`).
3. **Counts-only summary** — `entity_summary` is entity-type counts; no spans/values in meta (`entity_summary.py`).
4. **Double analyze cost** — Pipeline may call Presidio `analyze` for counts and again inside anonymize paths (honest inefficiency noted in `ARCHITECTURE.md`).
5. **Scheduler behavior** — When enabled, file-ingest interval job is always registered; Postgres cron job only if `POSTGRES_BATCH_CRON` and `postgres_batch.enabled` (`jobs/scheduler.py`).
6. **`tokenize` is a label** — Values become `<{FIELD}_TOKEN>`; not cryptographic or reversible tokens.

Parent view: [../2-containers.md](../2-containers.md). Diagram: [pii-gateway.mmd](pii-gateway.mmd).
