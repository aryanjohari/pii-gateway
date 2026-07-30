# C2 — Containers

Deployable and mountable pieces. This is the **default map** for the portfolio graph ([../architecture.graph.json](../architecture.graph.json)).

| ID | What runs | Role |
|----|-----------|------|
| `pii-gateway` | FastAPI + Uvicorn in one Docker service | HTTP sanitize, internal job triggers, `/healthz`, optional in-process APScheduler, Presidio engines |
| `policy-file` | Mounted YAML/JSON | Non-secret redaction rules, named SQL, inbox paths |
| `local-volume` | Docker volume / host path | Default outbound artifacts + gateway state JSON |
| `postgres` | Optional external DB | Read-only named SQL exports (Compose example) |
| `s3-compatible` | Optional MinIO / R2 / AWS S3 | Inbox objects and/or outbound `put_object` |

**Not separate containers:** Presidio, spaCy, APScheduler, connectors — all in-process inside `pii-gateway`. There is no worker CLI.

Compose: [`docker-compose.yml`](../../docker-compose.yml) (app only); optional PG + MinIO in [`docker-compose.example.yml`](../../docker-compose.example.yml).

Diagram: [2-containers.mmd](2-containers.mmd). Zoom: [3-components/pii-gateway.md](3-components/pii-gateway.md).
