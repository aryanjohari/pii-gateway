# PII Gateway

Self-hosted API that redacts personal data from text and JSON using policy rules plus best-effort NLP. **[Live demo](https://pii-gateway.arkhives.nz/)** (sample data only).

```jsonc
// POST /v1/sanitize  (config/examples/config.example.yaml)
{ "text": "Contact Alice Johnson at alice@example.com for details.",
  "structured": { "email": "bob@example.com", "full_name": "Bob Smith", "plan": "pro" } }

// result
{ "text": "Contact <PERSON> at <EMAIL_ADDRESS> for details.",
  "structured": { "email": "<EMAIL_ADDRESS>", "full_name": "<PERSON>", "plan": "pro" } }
```

`email` and `full_name` are redacted by declared policy rules; names and emails in free text are caught by Presidio.

Self-hosted **PII sanitization gateway**: one Docker-first FastAPI service that redacts free text and nested JSON from a mounted **policy file** (deterministic field rules) with **Microsoft Presidio** as best-effort NLP on undeclared strings, then optionally writes artifacts to local disk or S3-compatible storage. Batch paths can pull PostgreSQL exports or CSV/JSON inbox files.

**Why:** Centralize scrubbing so analytics, logs, and experiments never need a copy of the same redaction logic in every repo. **Not** a compliance product, accuracy guarantee, or OLTP database proxy—policy-first; NLP misses are expected.

**Product surface:** landing + playground live under [`web/`](web/) (Vercel). Public demo proxies through a server-side BFF—**sample data only**. Home-lab API host checklist: [docs/DEPLOY_PI.md](docs/DEPLOY_PI.md).

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

### Landing page (local)

```bash
cd web
cp .env.example .env.local
# PII_GATEWAY_API_URL=http://127.0.0.1:8000
# PII_GATEWAY_API_KEY=<same-as-SANITIZE_HTTP_API_KEY>
npm install && npm run dev
```

See [`web/README.md`](web/README.md). Offline playground is expected until the gateway URL is configured.

### Container image (GHCR)

Multi-arch images (`linux/amd64`, `linux/arm64` for Raspberry Pi) publish on version tags via [`.github/workflows/publish-image.yml`](.github/workflows/publish-image.yml):

```bash
docker pull ghcr.io/aryanjohari/pii-gateway:latest
# or a release tag, e.g. ghcr.io/aryanjohari/pii-gateway:0.1.0
```

Until the first release workflow has run, build locally with `docker compose build` (works on amd64 and arm64 hosts).

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
| `S3_CONNECT_TIMEOUT_SECONDS` / `S3_READ_TIMEOUT_SECONDS` | S3 timeouts (defaults `5` / `60`). A timeout raises `TimeoutError` naming the operation, bucket and key. |
| `INBOX_S3_BUCKET` / `INBOX_S3_PREFIX` | Defaults when policy leaves S3 inbox empty. |
| `POSTGRES_BATCH_DSN` | Async SQLAlchemy URL (`postgresql+asyncpg://…`). Prefer read-only. |
| `POSTGRES_COMMAND_TIMEOUT_SECONDS` | Per-query timeout for the batch export (default `60`). A timeout raises `TimeoutError` naming the query. |
| `POSTGRES_BATCH_CRON` | Cron for scheduled Postgres batch; empty disables. |
| `BATCH_FILE_POLL_SECONDS` | File inbox poll interval (min 5s). |
| `INTERNAL_JOB_API_KEY` | Enables `/internal/jobs/*` (`X-Internal-Job-Key`). |
| `GATEWAY_STATE_DIR` | Cursors + processed-file index (persist across restarts). |
| `DISABLE_SCHEDULER` | `true` skips APScheduler. |
| `CORS_ALLOWED_ORIGINS` | Comma-separated; empty disables CORS middleware. |
| `BATCH_DEMO_FIXTURE` | Synthetic Postgres rows without a real DB. |
| `SANITIZE_RATE_LIMIT_PER_MINUTE` | Per-client IP cap on `/v1/sanitize` (default `60`; `0` disables). |
| `SANITIZE_MAX_BODY_BYTES` | Max `Content-Length` for sanitize (default `65536`; `0` disables). |
| `SANITIZE_MAX_CHARS` | Max total string characters in text+structured (default `10000`; `0` disables). |

Example policy shape:

```yaml
config_version: 1
redaction_entities: [EMAIL_ADDRESS, PERSON]
structured_field_rules:
  email: redact
  full_name: redact
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

**Placeholders:** Declared `redact` / `tokenize` and Presidio free-text output use the same angle-bracket style (e.g. `<EMAIL_ADDRESS>`, `<PERSON>`). Common field names map to Presidio entity types; unknown fields use `<{FIELD_UPPER}>`. `tokenize` is **not** cryptographic. `passthrough` and undeclared strings still run through best-effort Presidio NLP—prefer declared field rules for batch/tabular data.

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
| 413 | `payload_too_large` | Body or character budget exceeded |
| 429 | `rate_limited` | Per-IP sanitize rate limit exceeded |
| 503 | `misconfigured` | Server key unset/blank |
| 500 | `internal_error` | Sanitizer failure |

For a public playground or home-lab demo, use [`config/examples/config.demo.yaml`](config/examples/config.demo.yaml) (`write_raw` / `write_cleaned` false), set the rate/size limits above, `DISABLE_SCHEDULER=true`, and put your site origin in `CORS_ALLOWED_ORIGINS` (or call via a server-side BFF). This is **not** a compliance product—do not send real PII to a public demo. Raspberry Pi checklist: [docs/DEPLOY_PI.md](docs/DEPLOY_PI.md).

**After pulling demo policy changes:** remount/restart the Pi (or local Compose) so it picks up the updated `config.demo.yaml`—e.g. `docker compose -f docker-compose.yml -f docker-compose.demo.yml up -d --force-recreate` (or restart the gateway service after confirming the volume mount still points at `config/examples/config.demo.yaml`).

OpenAPI: `/docs` when the server is running.

### Batch & storage

- **Postgres:** enable in policy, set `POSTGRES_BATCH_DSN` (read-only), optionally `POSTGRES_BATCH_CRON` or `POST /internal/jobs/postgres-batch`. SQL is **named in the policy only**—not a generic DB proxy.
- **Files:** `batch_file_ingest.mode` `local` or `s3`; poll via scheduler or `POST /internal/jobs/file-ingest`. Accepts `.csv` / `.json` (JSON root must be an array of objects).
- **Artifacts:** `STORAGE_BACKEND=local|s3`; paths like `cleaned/http/YYYY/MM/DD/{uuid}.json` (HTTP) or `.jsonl` for batch. Persist `GATEWAY_STATE_DIR` across restarts.
- **Auth:** keep `/internal/jobs/*` off the public internet; set `INTERNAL_JOB_API_KEY` only when needed.

### Deploy notes

Compose-first (`docker-compose.yml`; optional Postgres+MinIO overlay; optional demo overlay `docker-compose.demo.yml`). The app listens on plain HTTP `:8000`—terminate TLS at a reverse proxy or Cloudflare Tunnel ([docs/DEPLOY_PI.md](docs/DEPLOY_PI.md)). Conceptual cloud paths (EC2, ECR/ECS + ALB) are the same container with env + volume mounts; no cloud IaC is required to run the core app.

Multi-arch GHCR publish: tag a release `v*` (or run **Publish image** workflow) → `ghcr.io/aryanjohari/pii-gateway` for `linux/amd64` and `linux/arm64`.

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

- **Unit** (`tests/unit/`): auth, config loader, text/structured sanitize, paths, CSV/JSON helpers, storage factory, rate limit, request limits, no-logging guard on core modules
- **Integration** (`tests/integration/`): `TestClient` against the real app (sanitize, limits, internal jobs, correlation ID)
- **CI** ([`.github/workflows/ci.yml`](.github/workflows/ci.yml)): Python 3.11/3.12 → spaCy model → ruff → mypy → pytest → `docker build` (3.12)

Contributing: [CONTRIBUTING.md](CONTRIBUTING.md).

---

## Evaluation

Presidio's detector (the `AnalyzerEngine` the API uses) scored on a hand-written synthetic dataset, using the entities in [`config.demo.yaml`](config/examples/config.demo.yaml). A prediction counts as correct when its type matches and it overlaps a labeled span; see [ADR 0004](docs/adr/0004-span-level-synthetic-eval.md).

| Entity | Labeled spans | False positives | Misses | Precision | Recall | F1 |
|---|---|---|---|---|---|---|
| `EMAIL_ADDRESS` | 25 | 0 | 0 | 1.00 | 1.00 | 1.00 |
| `PERSON` | 31 | 1 | 0 | 0.97 | 1.00 | 0.98 |
| `PHONE_NUMBER` | 24 | 0 | 0 | 1.00 | 1.00 | 1.00 |

Dataset: 90 sentences ([`eval/dataset.jsonl`](eval/dataset.jsonl)), 19 of them with no personal data. Reproduce with `python -m eval.run_eval`, which rewrites [`eval/results.md`](eval/results.md) (including per-sentence latency, which varies by machine).

**Limitations of this measurement:** synthetic, templated English sentences with fictional data, so real text will score lower; 24–31 examples per type is a small sample, and each type is only just past the ~20 needed to treat a per-type number as more than an anecdote; US-style phone formats only; no names, phones or addresses in NZ formats yet. The dataset was written before the first run and not changed afterwards.

---

## Limitations

- **Best-effort redaction.** Presidio NLP produces false negatives (missed personal data) and false positives. The [Evaluation](#evaluation) numbers come from clean synthetic sentences, so they are an optimistic baseline, not a promise for your data. Do not rely on it as the only control.
- **Not a legal or compliance product.** Redacted output can still identify a person when combined with other data. Using this service does not remove your obligations under privacy law (for example the NZ Privacy Act 2020); it can help reduce exposure as one technical control. See [docs/research/nz-privacy-compliance.md](docs/research/nz-privacy-compliance.md).
- **English only.** The NLP path loads English models.
- **Batch exports sit in memory.** Sanitized rows are collected in a list before the NDJSON artifact is written, so very large exports use a lot of memory.
- **Batch connectors are less tested** than the HTTP path (S3 inbox, scheduler, Postgres job).

## Architecture

Design case study and tradeoffs: **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)**  
C4 diagrams (canonical): **[docs/c4/](docs/c4/)** · zoom map [docs/c4/portfolio-map.json](docs/c4/portfolio-map.json)  
Browser viewer (C2 flowchart alias): [docs/view-architecture.html](docs/view-architecture.html) (`cd docs && python3 -m http.server 8765`)  
Narrative overview: [PROJECT.md](PROJECT.md)

---

## License

MIT — see [LICENSE](LICENSE).
