# PII Gateway

Self-hosted **PII sanitization gateway**: FastAPI HTTP API (JSON), Microsoft Presidio, optional **Postgres** batch export, **CSV / JSON array** file ingest, and pluggable **local or S3-compatible** artifact storage. Configuration is **environment variables** plus a **mounted YAML/JSON policy file** (no secrets in Git).

## Five-minute quickstart

1. Copy env and policy examples:

   ```bash
   cp .env.example .env
   cp config/examples/config.example.yaml ./config.yaml
   ```

2. Set `SANITIZE_HTTP_API_KEY` in `.env` and point `PII_GATEWAY_CONFIG_PATH` at your policy file (or use the compose default mount).

3. Start with Docker Compose:

   ```bash
   docker compose up --build
   ```

4. Call the API:

   ```bash
   curl -sS -X POST http://localhost:8000/v1/sanitize \
     -H "Content-Type: application/json" \
     -H "X-API-Key: YOUR_KEY" \
     -d '{"text":"Email alice@example.com"}' | jq .
   ```

5. Health check: `GET http://localhost:8000/healthz`

**Optional full stack** (Postgres + MinIO + gateway) — adapt credentials and buckets, then:

```bash
docker compose -f docker-compose.yml -f docker-compose.example.yml up --build
```

## Local development

- Python **3.11+**
- `python -m venv .venv && source .venv/bin/activate`
- `pip install -e ".[dev]"`
- `pytest` · `ruff check src tests` · `mypy src`
- `DISABLE_SCHEDULER=true` avoids background jobs during tests (see `.env.example`).

Run the app:

```bash
export SANITIZE_HTTP_API_KEY=dev
export STORAGE_LOCAL_PATH=./data/out
export GATEWAY_STATE_DIR=./data/state
uvicorn pii_gateway.main:app --reload
```

## HTTP API

- `POST /v1/sanitize` — JSON body with at least one of `text` or `structured`. Responses use a stable envelope: `ok`, `correlation_id`, `adapter`, `config_version`, `result`, `meta` (no raw PII in success paths).
- `GET /healthz` — liveness.
- `POST /internal/jobs/postgres-batch` and `POST /internal/jobs/file-ingest` — require `INTERNAL_JOB_API_KEY` (`X-Internal-Job-Key`); **bind to private networks** or disable by leaving the key unset.

Auth: `X-API-Key` **or** HTTP Basic when `BASIC_AUTH_USER` / `BASIC_AUTH_PASSWORD` are set. If neither API key nor Basic is configured, the API is open (development only).

## Batch and scheduling

- **In-process**: APScheduler runs a **file inbox** poll on `batch_file_ingest.poll_seconds` (overridable via `BATCH_FILE_POLL_SECONDS`). Postgres batch uses `POSTGRES_BATCH_CRON` when enabled in policy.
- **External cron**: call the internal HTTP endpoints with the internal job key instead of running the scheduler.
- **CI / demos**: `BATCH_DEMO_FIXTURE=true` feeds synthetic Postgres-style rows **without** a real DSN (runs before normal Postgres batch logic).

**Postgres cursor**: last successful batch time is stored under `GATEWAY_STATE_DIR` in `postgres_batch_cursor.json` as `last_run` (ISO timestamp), bound as `:since` for queries that declare `params_from: last_run_cursor`.

## Threat model (summary)

- The gateway is **not** a safe OLTP database proxy. Batch access should use **read-only** credentials and **reviewed, parameterized** SQL from the policy file only.
- **Never log raw bodies**, row payloads, or file contents. Logs are structured JSON to stdout (correlation IDs, adapter names, config version, durations, counts, safe error codes).
- Mount **`.env`** or platform secrets so credentials exist only as environment variables at runtime; do not commit `.env`.
- For production, terminate **TLS** at a reverse proxy (Caddy, Traefik, nginx), add **rate limits**, and optionally an **OAuth2 proxy** in front of the API.

## Production checklist

- [ ] Strong `SANITIZE_HTTP_API_KEY` (or Basic) configured; internal job key set only if internal routes are needed.
- [ ] `PII_GATEWAY_CONFIG_PATH` mounted read-only; SQL queries reviewed in Git.
- [ ] `STORAGE_BACKEND` and paths/buckets correct; S3 endpoint set for MinIO/R2 when applicable.
- [ ] Postgres DSN uses a **read-only** role; `POSTGRES_BATCH_CRON` appropriate for load.
- [ ] Disk/volumes for `STORAGE_LOCAL_PATH`, inbox, and `GATEWAY_STATE_DIR` sized and backed up per policy.
- [ ] Reverse proxy: TLS, timeouts, rate limit, optional OAuth2 proxy.
- [ ] Log aggregation consumes stdout only; verify redaction rules in staging.

## License

MIT — see [LICENSE](LICENSE). Contributions: [CONTRIBUTING.md](CONTRIBUTING.md).
