# PII Gateway

Visitor overview: see [`portfolio.yaml`](portfolio.yaml).

Self-hosted **PII sanitization gateway**: one Docker-first FastAPI service that redacts free text and nested JSON with **Microsoft Presidio** plus a mounted **policy file**, then optionally writes artifacts to local disk or S3-compatible storage. Batch paths can pull PostgreSQL exports or CSV/JSON inbox files.

**Why:** Centralize scrubbing so analytics, logs, and experiments never need a copy of the same redaction logic in every repo. Not a compliance product or OLTP database proxy.

---

## Features (verified in this repo)

- `POST /v1/sanitize` — live text and/or nested JSON; `X-API-Key` auth (missing server key → 503)
- Mounted YAML/JSON **policy**: entity types, per-field rules (`redact` / `tokenize` / `mask` / `passthrough`), persistence flags
- **Fail-closed structured walk** — undeclared string fields still go through Presidio
- Optional **Postgres batch** (named SQL from policy only) and **file inbox** (local or S3-compatible)
- Optional **APScheduler** cron/interval jobs; one-shot triggers under `/internal/jobs/*`
- Outbound **local** or **S3-compatible** artifacts under date-partitioned UUID paths
- Structured JSON logs; core sanitize modules guarded against logging imports
- `GET /healthz`, Docker Compose, GitHub Actions CI (lint, mypy, pytest, image build)

---

## Quick start

**Prerequisites:** Docker + Compose v2, Git.

```bash
git clone https://github.com/aryanjohari/pii-gateway.git
cd pii-gateway
cp .env.example .env
# Set SANITIZE_HTTP_API_KEY to a long random secret in .env
docker compose up --build
```

Default Compose mounts `config/examples/config.example.yaml` as the policy. Wait for healthy, then:

```bash
curl -sS -X POST http://localhost:8000/v1/sanitize \
  -H "Content-Type: application/json" \
  -H "X-API-Key: <same-as-SANITIZE_HTTP_API_KEY>" \
  -d '{"text":"Contact alice@example.com for details."}'

curl -sS http://localhost:8000/healthz
```

Optional Postgres + MinIO overlay:

```bash
docker compose -f docker-compose.yml -f docker-compose.example.yml up --build
```

### Local Python (maintainers)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
python -m spacy download en_core_web_sm
export SANITIZE_HTTP_API_KEY=dev
export STORAGE_LOCAL_PATH=./data/out
export GATEWAY_STATE_DIR=./data/state
export DISABLE_SCHEDULER=true
uvicorn pii_gateway.main:app --reload
```

---

## Config / env

**Secrets & runtime → environment** (see [`.env.example`](.env.example)). **Non-secret policy → mounted YAML/JSON** via `PII_GATEWAY_CONFIG_PATH`.

| Variable | Purpose |
|----------|---------|
| `PII_GATEWAY_CONFIG_PATH` | Policy file path inside the container (mount read-only). |
| `SANITIZE_HTTP_API_KEY` | Required for `/v1/sanitize` (`X-API-Key`). Empty/unset → **503**. |
| `STORAGE_BACKEND` | `local` or `s3`. |
| `STORAGE_LOCAL_PATH` | Local artifact root (e.g. `/data/out`). |
| `S3_ENDPOINT_URL` / `S3_BUCKET` / `S3_PREFIX` | S3-compatible outbound (omit endpoint for AWS default). |
| `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` / `AWS_REGION` | Shared by inbox download and outbound upload. |
| `INBOX_S3_BUCKET` / `INBOX_S3_PREFIX` | Defaults when policy leaves S3 inbox empty. |
| `POSTGRES_BATCH_DSN` | Async SQLAlchemy URL (`postgresql+asyncpg://…`). Prefer read-only. |
| `POSTGRES_BATCH_CRON` | Cron for scheduled Postgres batch; empty disables. |
| `BATCH_FILE_POLL_SECONDS` | File inbox poll interval (min 5s). |
| `INTERNAL_JOB_API_KEY` | Enables `/internal/jobs/*` (`X-Internal-Job-Key`). |
| `GATEWAY_STATE_DIR` | Cursors + processed-file index (persist across restarts). |
| `DISABLE_SCHEDULER` | `true` skips APScheduler. |
| `CORS_ALLOWED_ORIGINS` | Comma-separated; empty disables CORS middleware. |
| `BATCH_DEMO_FIXTURE` | Synthetic Postgres rows without a real DB. |

Example policy shape:

```yaml
config_version: 1
redaction_entities: [EMAIL_ADDRESS, PERSON]
structured_field_rules:
  email: redact
  full_name: tokenize
postgres_batch:
  enabled: false
  query_name: export_users
  queries:
    export_users:
      sql: "SELECT id, email, full_name, note FROM app.users WHERE updated_at > :since"
      params_from: last_run_cursor
batch_file_ingest:
  mode: local
  local_path: /data/inbox
  poll_seconds: 60
persistence:
  write_raw: false
  write_cleaned: true
```

**Note:** `passthrough` and undeclared string fields still run through Presidio free-text redaction. `tokenize` produces a field-name label (`<{FIELD}_TOKEN>`), not a reversible token.

### Real-time API

`POST /v1/sanitize` — send at least one of `text` or `structured`:

```bash
curl -sS -X POST http://localhost:8000/v1/sanitize \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_KEY_HERE" \
  -H "X-Correlation-ID: optional-client-trace-id" \
  -d '{
    "text": "Email alice@example.com",
    "structured": {"email": "bob@example.com", "full_name": "Bob Smith"}
  }'
```

Success shape:

```json
{
  "ok": true,
  "correlation_id": "…",
  "adapter": "http_json",
  "config_version": 1,
  "result": { "text": "…", "structured": { } },
  "meta": { "entity_summary": { "EMAIL_ADDRESS": 2 }, "duration_ms": 42 }
}
```

`meta.entity_summary` is **counts only** (safe to log). Forward **`result`** downstream. If `persistence.write_raw` is true, artifacts contain **pre-sanitization PII**—keep it false unless you need audit copies.

| Status | `error.code` | When |
|--------|--------------|------|
| 422 | `validation_error` | Bad body |
| 401 | `unauthorized` | Wrong/missing key (server key is set) |
| 503 | `misconfigured` | Server key unset/blank |
| 500 | `internal_error` | Sanitizer failure |

OpenAPI: `/docs` when the server is running.

### Batch & storage

- **Postgres:** enable in policy, set `POSTGRES_BATCH_DSN` (read-only), optionally `POSTGRES_BATCH_CRON` or `POST /internal/jobs/postgres-batch`. SQL is **named in the policy only**—not a generic DB proxy.
- **Files:** `batch_file_ingest.mode` `local` or `s3`; poll via scheduler or `POST /internal/jobs/file-ingest`. Accepts `.csv` / `.json` (JSON root must be an array of objects).
- **Artifacts:** `STORAGE_BACKEND=local|s3`; paths like `cleaned/http/YYYY/MM/DD/{uuid}.json` (HTTP) or `.jsonl` for batch. Persist `GATEWAY_STATE_DIR` across restarts.
- **Auth:** keep `/internal/jobs/*` off the public internet; set `INTERNAL_JOB_API_KEY` only when needed.

### Deploy notes

Compose-first (`docker-compose.yml`; optional Postgres+MinIO overlay). The app listens on plain HTTP `:8000`—terminate TLS at a load balancer or reverse proxy. Conceptual paths (EC2, ECR/ECS + ALB) are the same container with env + volume mounts; no Terraform is required to run the core app.

### HTTP surface

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| `POST` | `/v1/sanitize` | `X-API-Key` | Real-time sanitization. |
| `GET` | `/healthz` | None | Liveness. |
| `POST` | `/internal/jobs/postgres-batch` | `X-Internal-Job-Key` | Run Postgres batch once. |
| `POST` | `/internal/jobs/file-ingest` | `X-Internal-Job-Key` | Run file inbox scan once. |

---

## Tests / CI

```bash
pytest
ruff check src tests
mypy src
```

- **Unit** (`tests/unit/`): auth, config loader, text/structured sanitize, paths, CSV/JSON helpers, storage factory, no-logging guard on core modules
- **Integration** (`tests/integration/`): `TestClient` against the real app (sanitize, internal jobs, correlation ID)
- **CI** ([`.github/workflows/ci.yml`](.github/workflows/ci.yml)): Python 3.11/3.12 → spaCy model → ruff → mypy → pytest → `docker build` (3.12)

Contributing: [CONTRIBUTING.md](CONTRIBUTING.md).

---

## Architecture

Design case study and tradeoffs: **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)**  
Mermaid source (portfolio diagram): **[docs/architecture.mmd](docs/architecture.mmd)**  
Browser viewer: [docs/view-architecture.html](docs/view-architecture.html) (`cd docs && python3 -m http.server 8765`)  
Narrative overview: [PROJECT.md](PROJECT.md)

---

## License

MIT — see [LICENSE](LICENSE).
