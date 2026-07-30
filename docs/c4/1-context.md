# C1 — System Context

**System:** PII Gateway — one self-hosted service that redacts personal data from free text and nested JSON before downstream use.

**People (evidence)**

| Label | Role | Evidence |
|-------|------|----------|
| App integrator | Calls realtime sanitize | `api/routes_sanitize.py` — `POST /v1/sanitize`, `X-API-Key` |
| Automation caller | Triggers jobs or relies on scheduler | `api/routes_internal.py`; `jobs/scheduler.py` |
| Operator | Compose, policy mount, env secrets | `docker-compose.yml`, `settings.py`, `PII_GATEWAY_CONFIG_PATH` |

**External systems (optional unless noted)**

| Label | Role | Evidence |
|-------|------|----------|
| PostgreSQL | Named, parameterized batch SQL from policy | `connectors/batch_postgres_sqlalchemy.py`, `POSTGRES_BATCH_DSN` |
| S3-compatible storage | Inbox objects and/or outbound artifacts | `connectors/s3_inbox.py`, `storage/s3_compatible_backend.py` |
| Local volume | Default outbound + `GATEWAY_STATE_DIR` | `storage/local_volume_backend.py`, `state_store.py` |

**Notes**

- Presidio and spaCy run **inside** the gateway process (libraries), not as separate context systems.
- No public demo URL or hosted multi-tenant control plane in this repo.
- Compose default (`docker-compose.yml`) is gateway-only; Postgres + MinIO appear in `docker-compose.example.yml`.

Diagram: [1-context.mmd](1-context.mmd). Next: [2-containers](2-containers.md).
