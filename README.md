# PII Gateway

Self-hosted **PII sanitization gateway** for structured and free-text data. Operators run a **single Docker-first** service (FastAPI) that applies **Microsoft Presidio** NLP analysis plus **config-driven rules** for JSON fields. Inputs may be **real-time HTTP JSON**, **PostgreSQL** batch exports, or **CSV / JSON-array** files from a **local directory** or **S3-compatible** storage. Sanitized artifacts are written through a small **outbound storage interface** to **local disk** or **S3-compatible** buckets.

**Why use it:** Keep sensitive data out of downstream systems by centralizing redaction/tokenization behind one API and one policy file, with **12-Factor** configuration (**environment variables** for secrets, **mounted YAML/JSON** for policy), suitable for Compose, Kubernetes, or PaaS.

---

## Table of contents

1. [What & why](#1-what--why)
2. [Quickstart (5-minute setup)](#2-quickstart-5-minute-setup)
3. [Configuration model (for integrators)](#3-configuration-model-for-integrators)
4. [Real-time API (integration guide)](#4-real-time-api-integration-guide)
5. [Batch ingestion & storage](#5-batch-ingestion--storage)
6. [Microservice network integration (Docker)](#6-microservice-network-integration-docker)
7. [Operational notes](#7-operational-notes)
8. [Reference: HTTP surface](#8-reference-http-surface)
9. [License & contributing](#9-license--contributing)

---

## 1. What & why

| Aspect | Description |
|--------|-------------|
| **Runtime** | One **container** runs **FastAPI**, **Presidio** `AnalyzerEngine` / `AnonymizerEngine` (singletons via app lifespan), optional **APScheduler** jobs. |
| **Policy** | Non-secret rules live in **`PII_GATEWAY_CONFIG_PATH`** (YAML or JSON): entity types, per-field structured rules, batch query names, file inbox mode. |
| **Secrets & connections** | **Only** via environment variables (e.g. `.env` mounted in Compose)—DSN, API keys, S3 credentials. |
| **Extensibility mental model** | **Inbound connectors** (HTTP, PostgreSQL stream, file inbox) normalize inputs into **records**; the **sanitization core** runs Presidio on text and applies **`structured_field_rules`** to JSON-like objects; **outbound storage** persists optional **`raw`** / **`cleaned`** layers under stable paths. |

**Non-goals:** This is **not** a safe OLTP database proxy. Batch SQL must be **reviewed, parameterized**, and run with **read-only** credentials.

---

## 2. Quickstart (5-minute setup)

### Prerequisites

- **Docker** and **Docker Compose** v2
- **Git**

### Steps

**1. Clone the repository**

```bash
git clone https://github.com/<your-org>/pii-gateway.git
cd pii-gateway
```

**2. Create environment and policy files**

```bash
cp .env.example .env
cp config/examples/config.example.yaml ./config.yaml
```

**3. Set required variables in `.env`**

At minimum, set a strong HTTP API key (used by `POST /v1/sanitize`):

```bash
# In .env (compose also sets PII_GATEWAY_CONFIG_PATH on the service)
SANITIZE_HTTP_API_KEY=<generate-a-long-random-secret>
```

**4. Start the stack (build from this repo’s `Dockerfile`)**

Default `docker-compose.yml` mounts **`config/examples/config.example.yaml`** into the container as `/etc/pii-gateway/config.yaml` and sets `PII_GATEWAY_CONFIG_PATH` accordingly. To use your own policy, change the volume line in `docker-compose.yml` to mount `./config.yaml` (or any path on the host) to `/etc/pii-gateway/config.yaml:ro`.

```bash
docker compose up --build
```

Wait until the container is healthy (`/healthz`).

**5. Call the sanitize API**

```bash
curl -sS -X POST http://localhost:8000/v1/sanitize \
  -H "Content-Type: application/json" \
  -H "X-API-Key: <same-as-SANITIZE_HTTP_API_KEY>" \
  -d '{"text":"Contact alice@example.com for details."}'
```

**6. Health check**

```bash
curl -sS http://localhost:8000/healthz
```

Expected:

```json
{"status":"ok"}
```

### Optional full stack (Postgres + MinIO + gateway)

Use the bundled example overlay (adjust credentials and buckets for production):

```bash
docker compose -f docker-compose.yml -f docker-compose.example.yml up --build
```

---

## 3. Configuration model (for integrators)

### 3.1 Environment variables (secrets & runtime)

Canonical names (see `.env.example` for the full list):

| Variable | Purpose |
|----------|---------|
| `PII_GATEWAY_CONFIG_PATH` | Path **inside the container** to the policy file (mount read-only). |
| `SANITIZE_HTTP_API_KEY` | API key for `POST /v1/sanitize` (header `X-API-Key`). |
| `BASIC_AUTH_USER` / `BASIC_AUTH_PASSWORD` | Optional HTTP Basic instead of API key. |
| `STORAGE_BACKEND` | `local` or `s3` — selects outbound implementation. |
| `STORAGE_LOCAL_PATH` | Root directory for `local` backend (e.g. `/data/out`). |
| `S3_ENDPOINT_URL` | Optional; set for MinIO, R2, etc. Omit for AWS S3 default endpoint. |
| `S3_BUCKET` / `S3_PREFIX` | Outbound bucket and key prefix when `STORAGE_BACKEND=s3`. |
| `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` / `AWS_REGION` | S3-compatible (or AWS) credentials used by **both** inbox listing/download and outbound upload in the current implementation. |
| `INBOX_S3_BUCKET` / `INBOX_S3_PREFIX` | Default inbox bucket/prefix when policy does not set them (S3 file mode). |
| `POSTGRES_BATCH_DSN` | SQLAlchemy **async** URL, e.g. `postgresql+asyncpg://user:pass@host:5432/db`. |
| `POSTGRES_BATCH_CRON` | Cron expression (e.g. `0 * * * *`) to run Postgres batch when enabled in policy. Empty disables scheduled Postgres batch. |
| `BATCH_FILE_POLL_SECONDS` | Overrides policy `batch_file_ingest.poll_seconds` floor (minimum 5 seconds enforced). |
| `INTERNAL_JOB_API_KEY` | Enables `POST /internal/jobs/*` when set; clients send `X-Internal-Job-Key`. |
| `GATEWAY_STATE_DIR` | Directory for cursors and processed-file indexes (use a **persistent volume** in production). |
| `DISABLE_SCHEDULER` | `true` skips APScheduler (tests / API-only). |
| `CORS_ALLOWED_ORIGINS` | Comma-separated origins when browser clients call the API. |

### 3.2 Policy file schema (`config.yaml` / JSON)

The mounted file validates against the internal schema. Minimal shape:

```yaml
config_version: 1

redaction_entities:
  - EMAIL_ADDRESS
  - PERSON

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
  s3_bucket: ""
  s3_prefix: ""

persistence:
  write_raw: false
  write_cleaned: true
```

**`structured_field_rules` values:** `redact` | `tokenize` | `mask` | `passthrough`.

**`params_from` (Postgres):** `last_run_cursor` binds `:since` from the last successful batch timestamp, or `none` for no cursor parameter.

---

## 4. Real-time API (integration guide)

### 4.1 Endpoint

| Item | Value |
|------|--------|
| **Method / path** | `POST /v1/sanitize` |
| **Content-Type** | `application/json` |
| **Auth** | `X-API-Key: <SANITIZE_HTTP_API_KEY>` **or** HTTP Basic if configured. If neither API key nor Basic is configured, the route is **open** (development only). |

### 4.2 Request body

Provide **at least one** of `text` or `structured`:

```json
{
  "text": "Optional free text to analyze and redact.",
  "structured": {
    "email": "user@example.com",
    "full_name": "Jane Doe",
    "note": "Call me at 555-0100"
  }
}
```

Either field may be omitted; **both** may be present.

### 4.3 Example `curl` (success)

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

The server echoes or generates a correlation id (header **`X-Correlation-ID`** on the response).

### 4.4 Success response (JSON)

Shape (Pydantic models in `src/pii_gateway/api/schemas.py`):

```json
{
  "ok": true,
  "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
  "adapter": "http_json",
  "config_version": 1,
  "result": {
    "text": "<redacted text per Presidio + policy>",
    "structured": {
      "email": "<per structured_field_rules>",
      "full_name": "<per structured_field_rules>",
      "note": "<per structured_field_rules>"
    }
  },
  "meta": {
    "entity_summary": {
      "EMAIL_ADDRESS": 2,
      "PERSON": 1
    },
    "duration_ms": 42
  }
}
```

**Integrator notes:**

- Treat **`result`** as the **only** sanitized payload to forward downstream.
- **`meta.entity_summary`** aggregates Presidio entity counts (safe metadata).
- When `persistence.write_cleaned` is `true`, a **JSON artifact** is also written under `cleaned/http/<YYYY>/<MM>/<DD>/<correlation_id>.json` (local or S3, depending on `STORAGE_BACKEND`).

### 4.5 Error responses (JSON)

Validation failure (`422`):

```json
{
  "ok": false,
  "error": {
    "code": "validation_error",
    "message": "Invalid request body"
  }
}
```

Auth failure (`401` / `403`):

```json
{
  "ok": false,
  "error": {
    "code": "unauthorized",
    "message": "Invalid or missing API key"
  }
}
```

Internal sanitizer failure (`500`):

```json
{
  "ok": false,
  "error": {
    "code": "internal_error",
    "message": "Sanitization failed"
  }
}
```

---

## 5. Batch ingestion & storage

### 5.1 How “adapters” fit together

For **batch** workloads the codebase uses **inbound connectors** that all converge on the same sanitization path:

1. **PostgreSQL** — Streams rows from a **named, parameterized** SQL statement in the policy file. Rows are dicts; each row is passed through **structured-field sanitization** (and string values still participate in entity detection as implemented in the pipeline).
2. **File inbox (CSV / JSON array)** — Polls on a timer. **CSV** rows and **JSON array** elements become dict-like records. Outputs are written as **NDJSON** (`.jsonl` content-type) under the `cleaned` layer.
3. **Real-time HTTP** — Same core; response is JSON; optional artifact under `cleaned/http/...`.

**Outbound storage** is selected only from environment: `STORAGE_BACKEND=local` uses `STORAGE_LOCAL_PATH`; `STORAGE_BACKEND=s3` uses `S3_BUCKET`, `S3_PREFIX`, and AWS-compatible settings.

**Important:** S3 **inbox** listing and download use the **same** `S3_ENDPOINT_URL` and `AWS_*` credentials as outbound S3 in the current release. You may use **different buckets** (inbox vs outbound) on the same provider/account.

### 5.2 PostgreSQL batch

**`.env`**

```bash
POSTGRES_BATCH_DSN=postgresql+asyncpg://readonly:password@postgres.internal:5432/appdb
POSTGRES_BATCH_CRON=0 * * * *
```

**`config.yaml`**

```yaml
postgres_batch:
  enabled: true
  query_name: export_users
  queries:
    export_users:
      sql: "SELECT id, email, full_name, note FROM app.users WHERE updated_at > :since"
      params_from: last_run_cursor
```

**Behavior:** Cursor state is stored in `GATEWAY_STATE_DIR/postgres_batch_cursor.json`. After each successful run, `last_run` advances.

**Manual trigger (optional):** If `INTERNAL_JOB_API_KEY` is set:

```bash
curl -sS -X POST http://localhost:8000/internal/jobs/postgres-batch \
  -H "X-Internal-Job-Key: YOUR_INTERNAL_KEY"
```

### 5.3 Local file inbox (CSV / JSON array)

**Compose:** Mount a host directory to the container path referenced by `local_path`.

**`config.yaml`**

```yaml
batch_file_ingest:
  mode: local
  local_path: /data/inbox
  poll_seconds: 60
```

**Files:** `.csv` and `.json` where the JSON document’s **root is an array of objects**. Non-matching extensions are skipped.

### 5.4 S3-compatible file inbox

**`.env`** (bucket can also be set in policy; env provides defaults)

```bash
INBOX_S3_BUCKET=my-inbox-bucket
INBOX_S3_PREFIX=uploads/
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_REGION=us-east-1
# Omit S3_ENDPOINT_URL for default AWS S3 endpoints
```

For MinIO (example):

```bash
S3_ENDPOINT_URL=http://minio:9000
AWS_ACCESS_KEY_ID=minio
AWS_SECRET_ACCESS_KEY=minio12345
AWS_REGION=us-east-1
INBOX_S3_BUCKET=inbox
```

**`config.yaml`**

```yaml
batch_file_ingest:
  mode: s3
  local_path: /data/inbox
  poll_seconds: 120
  s3_bucket: ""
  s3_prefix: ""
```

If `s3_bucket` / `s3_prefix` are empty strings, the values from `INBOX_S3_BUCKET` / `INBOX_S3_PREFIX` are used.

**Manual file ingest trigger:**

```bash
curl -sS -X POST http://localhost:8000/internal/jobs/file-ingest \
  -H "X-Internal-Job-Key: YOUR_INTERNAL_KEY"
```

### 5.5 Outbound storage: local vs S3

**Local (default)**

```bash
STORAGE_BACKEND=local
STORAGE_LOCAL_PATH=/data/out
```

**S3-compatible**

```bash
STORAGE_BACKEND=s3
S3_BUCKET=my-clean-artifacts
S3_PREFIX=pii-gateway/
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_REGION=us-east-1
# S3_ENDPOINT_URL=  # omit for AWS; set for MinIO/R2
```

**Persistence flags (`config.yaml`)**

```yaml
persistence:
  write_raw: false
  write_cleaned: true
```

Artifact layout (conceptual): `cleaned/<source>/<YYYY>/<MM>/<DD>/<id>.<ext>` where `<source>` is e.g. `http`, `postgres`, or batch file source labels used by jobs.

---

## 6. Microservice network integration (Docker)

When another **container** needs to call the gateway on the **same Docker Compose network**, use the **Compose service name** as hostname and **internal port 8000**.

**Example:** If `docker-compose.yml` defines:

```yaml
services:
  pii-gateway:
    build: .
    ports:
      - "8000:8000"
```

A sibling service `app` in the **same** Compose project can call:

```text
http://pii-gateway:8000/v1/sanitize
```

**Example `curl` from another container (shell for illustration):**

```bash
curl -sS -X POST http://pii-gateway:8000/v1/sanitize \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_KEY_HERE" \
  -d '{"text":"sensitive string"}'
```

**Integration checklist:**

- Attach both services to the **same user-defined bridge network** (Compose does this by default within one file).
- Do **not** rely on `localhost` from another container—use the **service DNS name**.
- Pass the API key via **secrets** / env injected into the client container.
- Terminate **TLS** at an edge proxy when exposing beyond the internal network.

---

## 7. Operational notes

- **Scheduler:** APScheduler runs **file inbox** polling on the configured interval. Postgres batch runs only when `POSTGRES_BATCH_CRON` is set **and** `postgres_batch.enabled` is `true`.
- **State disk:** Persist **`GATEWAY_STATE_DIR`** (cursor + processed file fingerprints) across restarts.
- **Security:** Keep internal job routes off the public internet; set `INTERNAL_JOB_API_KEY` only when needed. Prefer **read-only** DB roles for batch DSNs.
- **Pre-built images:** This README assumes `docker compose up --build`. Publishing to a registry (`docker pull`) is optional; add a CI workflow that pushes `ghcr.io/...` or Docker Hub and document the image tag alongside `docker run` / Compose `image:` overrides.

---

## 8. Reference: HTTP surface

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| `POST` | `/v1/sanitize` | API key or Basic | Real-time sanitization. |
| `GET` | `/healthz` | None | Liveness. |
| `POST` | `/internal/jobs/postgres-batch` | `X-Internal-Job-Key` | Run Postgres batch once. |
| `POST` | `/internal/jobs/file-ingest` | `X-Internal-Job-Key` | Run file inbox scan once. |

---

## 9. License & contributing

**License:** MIT — see [LICENSE](LICENSE).

**Contributing:** See [CONTRIBUTING.md](CONTRIBUTING.md).

---

## Local development (maintainers)

- Python **3.11+**
- `python -m venv .venv && source .venv/bin/activate`
- `pip install -e ".[dev]"`
- Install spaCy model: `python -m spacy download en_core_web_sm`
- `pytest` · `ruff check src tests` · `mypy src`
- `DISABLE_SCHEDULER=true` avoids background jobs during local API hacking.

```bash
export SANITIZE_HTTP_API_KEY=dev
export STORAGE_LOCAL_PATH=./data/out
export GATEWAY_STATE_DIR=./data/state
uvicorn pii_gateway.main:app --reload
```
