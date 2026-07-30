# C2 — Containers

Deployable and mountable pieces. **Canonical** container diagram for portfolio (`portfolio.yaml` → `diagram:`). Zoom index: [portfolio-map.json](portfolio-map.json).

| ID | What runs | Role | Evidence |
|----|-----------|------|----------|
| `pii-gateway` | FastAPI + Uvicorn in one Docker service | HTTP sanitize, internal job triggers, `/healthz`, optional in-process APScheduler, Presidio engines | `Dockerfile`, `main.py`, `docker-compose.yml` |
| `policy-file` | Mounted YAML/JSON | Non-secret redaction rules, named SQL, inbox paths | `config_loader.py`, `policy_schema.py`, Compose volume mount |
| `local-volume` | Docker volume / host path | Default outbound artifacts + gateway state JSON | `STORAGE_LOCAL_PATH`, `GATEWAY_STATE_DIR`, `storage/local_volume_backend.py` |
| `postgres` | Optional external DB | Read-only named SQL exports | `POSTGRES_BATCH_DSN`, `docker-compose.example.yml` |
| `s3-compatible` | Optional MinIO / R2 / AWS S3 | Inbox objects and/or outbound `put_object` | `STORAGE_BACKEND=s3`, `inbox_s3_*`, example MinIO service |

**Collapsed into `pii-gateway` (see C3, not separate containers):** Presidio, spaCy, APScheduler, connectors, sanitize pipeline, auth helpers, correlation middleware. There is no worker CLI or second process.

**Notes**

- Default Compose runs **only** `pii-gateway` + a data volume; Postgres/MinIO are optional via the example overlay.
- When `STORAGE_BACKEND=s3`, outbound artifacts leave the local volume path; state files still use `GATEWAY_STATE_DIR` on disk.

Diagram: [2-containers.mmd](2-containers.mmd). Zoom: [3-components/pii-gateway.md](3-components/pii-gateway.md).
