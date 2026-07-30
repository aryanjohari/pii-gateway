# C3 — Components: `pii-gateway`

Zoom of the single FastAPI container. All of these share one process and one Docker image.

| ID | Code area | Role |
|----|-----------|------|
| Sanitize API | `api/routes_sanitize.py` | `POST /v1/sanitize` |
| Internal jobs API | `api/routes_internal.py` | `POST /internal/jobs/postgres-batch`, `POST /internal/jobs/file-ingest` |
| Healthz | `main.py` | `GET /healthz` |
| Auth + correlation | `api/auth.py`, `api/middleware.py` | API keys; correlation ID header |
| Policy loader | `config_loader.py`, `policy_schema.py` | Mounted policy at lifespan start |
| Sanitize pipeline | `core/sanitize_*.py` | Text + recursive structured redaction |
| Presidio engines | lifespan in `main.py` | Analyzer/Anonymizer once per process |
| Connectors | `connectors/` | Postgres, CSV, JSON array, S3 inbox |
| Jobs + scheduler | `jobs/` | Batch runners; optional APScheduler |
| Storage + state | `storage/`, `state_store.py` | Outbound local/S3; cursors and processed-file index |

Parent view: [../2-containers.md](../2-containers.md). Diagram: [pii-gateway.mmd](pii-gateway.mmd).
