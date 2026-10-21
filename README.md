# PII Gateway

Self-hosted API that redacts personal data from text and JSON using policy rules plus best-effort NLP. **[Live demo](https://pii-gateway.arkhives.nz/)** (sample data only).

> **Status**
> - A portfolio project. Not yet used in my own projects; dogfooding is planned.
> - The evaluation data is synthetic and written by the same person who wrote the recognisers, so the numbers are an optimistic baseline.
> - Best-effort redaction, not a compliance product. NLP misses are expected.
> - No external users yet.

```jsonc
// POST /v1/sanitize  (config/examples/config.example.yaml)
{ "text": "Contact Alice Johnson at alice@example.com for details.",
  "structured": { "email": "bob@example.com", "full_name": "Bob Smith", "plan": "pro" } }

// result
{ "text": "Contact <PERSON> at <EMAIL_ADDRESS> for details.",
  "structured": { "email": "<EMAIL_ADDRESS>", "full_name": "<PERSON>", "plan": "pro" } }
```

`email` and `full_name` are redacted by declared policy rules; names and emails in free text are caught by Presidio.

Calling an LLM? Point your SDK's `base_url` at this gateway's `/v1/chat/completions` and prompts are redacted before they leave your network. See [LLM proxy](#llm-proxy-openai-compatible).

Self-hosted **PII sanitization gateway**: one Docker-first FastAPI service that redacts free text and nested JSON from a mounted **policy file** (deterministic field rules) with **Microsoft Presidio** as best-effort NLP on undeclared strings, then optionally writes artifacts to local disk or S3-compatible storage. Batch paths can pull PostgreSQL exports or CSV/JSON inbox files.

**Why:** Centralize scrubbing so analytics, logs, and experiments never need a copy of the same redaction logic in every repo. **Not** a compliance product, accuracy guarantee, or OLTP database proxy—policy-first; NLP misses are expected.

**Product surface:** landing + playground live under [`web/`](web/) (Vercel). Public demo proxies through a server-side BFF—**sample data only**. Home-lab API host checklist: [docs/DEPLOY_PI.md](docs/DEPLOY_PI.md).

---

## Features (verified in this repo)

- `POST /v1/sanitize` — live text and/or nested JSON; `X-API-Key` auth (missing server key → 503)
- `POST /v1/chat/completions` — OpenAI-compatible proxy: redacts message text, forwards to the upstream LLM you configure (streaming supported; see [LLM proxy](#llm-proxy-openai-compatible))
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
python -m spacy download en_core_web_lg
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
| `TRUSTED_PROXY_HEADER` | Header holding the real client IP behind a reverse proxy (e.g. `CF-Connecting-IP`); the rate limit then buckets on it. Default empty = direct client host. Set only if your proxy overwrites that header and the app is unreachable around it, else clients can spoof it. |
| `SANITIZE_MAX_BODY_BYTES` | Max `Content-Length` for sanitize (default `65536`; `0` disables). |
| `LLM_UPSTREAM_BASE_URL` | Upstream for `/v1/chat/completions`, including the version prefix (e.g. `https://api.openai.com/v1`). Unset → **503**. Set by the operator only; never read from a request. |
| `LLM_UPSTREAM_TIMEOUT_SECONDS` | Wait for the upstream before returning **504** (default `60`). |
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

For a public playground or home-lab demo, use [`config/examples/config.demo-nz.yaml`](config/examples/config.demo-nz.yaml) (the entities in `config.demo.yaml` plus the NZ identifiers; `write_raw` / `write_cleaned` false), set the rate/size limits above, `DISABLE_SCHEDULER=true`, and put your site origin in `CORS_ALLOWED_ORIGINS` (or call via a server-side BFF). This is **not** a compliance product—do not send real PII to a public demo. Raspberry Pi checklist: [docs/DEPLOY_PI.md](docs/DEPLOY_PI.md).

**After pulling demo policy changes:** remount/restart the Pi (or local Compose) so it picks up the updated `config.demo-nz.yaml`—e.g. `docker compose -f docker-compose.yml -f docker-compose.demo.yml up -d --force-recreate` (or restart the gateway service after confirming the volume mount still points at `config/examples/config.demo-nz.yaml`).

OpenAPI: `/docs` when the server is running.

### LLM proxy (OpenAI-compatible)

`POST /v1/chat/completions` accepts an OpenAI chat-completions request, replaces personal data in the message text using the same engine and policy as `/v1/sanitize`, forwards the cleaned request to `LLM_UPSTREAM_BASE_URL`, and returns the upstream's reply. A developer changes one base URL and their prompts are scrubbed before they leave your network. It only covers code that calls an API; it does nothing for people typing into a chat website.

Worked example (a clinic's internal tool), run against the gateway with [`config.nz-llm.yaml`](config/examples/config.nz-llm.yaml) and a local stub upstream that replies with exactly the text it received:

```bash
curl -sS http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "X-API-Key: <gateway key>" \
  -H "Authorization: Bearer <your upstream API key>" \
  -d '{"model":"gpt-4o-mini","messages":[{"role":"user","content":"Summarise: Patient Jane Smith (NHI ZAC5361) rang from 021 123 4567 about her results."}]}'
```

```text
Upstream saw: Summarise: Patient <PERSON> (NHI <NZ_NHI>) rang from <PHONE_NUMBER> about her results.
```

With the OpenAI Python SDK (tested with `openai` 2.48.0 against the stub upstream), change the base URL and add the gateway key as a header:

```python
client = OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="<your upstream API key>",
    default_headers={"X-API-Key": "<gateway key>"},
)
```

- **Keys.** The gateway checks `X-API-Key` (same key as `/v1/sanitize`). Your upstream key goes in `Authorization` and is forwarded as is; it is never logged or stored. `X-API-Key` is not forwarded. Tools that can only set one key field cannot use this route.
- **Upstream.** Set `LLM_UPSTREAM_BASE_URL` and `LLM_UPSTREAM_TIMEOUT_SECONDS`. The policy's `redaction_entities` decide what is replaced; `config.nz-llm.yaml` is the NZ pack plus `PERSON`. A policy with an empty `redaction_entities` runs every recogniser.
- **Redact only.** The reply keeps the placeholders (`<PERSON>`); originals are not restored. No artifacts are written for this route.
- **Fails closed.** If validation or redaction fails, nothing is forwarded. Upstream error bodies are replaced by a gateway error that names the upstream host and status, because providers can echo the prompt back.

| Status | `error.code` | When |
|--------|--------------|------|
| 401 | `unauthorized` / `missing_upstream_key` | Wrong or missing `X-API-Key` / no `Authorization` header |
| 413 | `payload_too_large` | Body or character budget exceeded (same limits as sanitize) |
| 422 | `unsupported_content_type`, `unsupported_field`, `invalid_json`, `invalid_request` | Request outside the supported subset |
| 429 | `rate_limited` | Shares the sanitize rate limit |
| 500 | `internal_error` | Redaction failed; nothing was forwarded |
| 502 / 504 | `upstream_unreachable`, `upstream_bad_response` / `upstream_timeout` | Upstream down, unusable reply, or too slow |
| upstream's status | `upstream_error` | Upstream returned 4xx/5xx |
| 503 | `misconfigured` | Gateway key or `LLM_UPSTREAM_BASE_URL` unset |

Errors use the OpenAI shape (`{"error": {"message", "type", "param", "code"}}`); the OpenAI Python SDK raised them as typed errors in testing.

**What is and is not scanned.** Scanned: string `content` and `text` parts of `system`, `developer`, `user`, `assistant` and `tool` messages. Everything else is **rejected with a 422, never forwarded unscanned**: image, audio and file parts, `tools`/`functions`/`tool_calls`, `name`, `stop`, `response_format`, `metadata`, `user`, and any other field outside a short allow-list (`model`, `messages`, `temperature`, `top_p`, `max_tokens`, `max_completion_tokens`, `n`). Identifier-style fields (`model`, a tool message's `tool_call_id`) are forwarded as sent, not scanned.

**Streaming.** `stream: true` is supported (and `stream_options`). The whole request is redacted before anything is sent; the upstream's events are then relayed as they arrive, so the time to the first event includes the redaction time above. Errors before the stream starts use the table above. If the upstream breaks mid-stream, the gateway ends the stream with an error event (`upstream_stream_interrupted`). If the caller disconnects, the upstream request is closed. Tested over real sockets with the OpenAI SDK against a stub upstream: events arrived about when the upstream sent them, and a disconnect reached the upstream. Reply events are not scanned.

**What it cannot do.**
- A missed entity reaches the LLM. Precision and recall are in [Evaluation](#evaluation) and [NZ identifiers](#nz-identifiers); those numbers come from synthetic sentences. In one probe, the Maori name "Aroha Ngata" was not detected as `PERSON` by the English spaCy model (one example, not a measurement).
- Multi-turn history is redacted message by message on every request, so a miss in an earlier turn is a miss each time it is replayed.
- The model's reply can repeat or infer details the placeholders hide; nothing checks the reply.
- It helps reduce exposure; it does not make output anonymous or compliant with any law.

**Latency added by the gateway** (local stub upstream, 200 sequential requests, macOS arm64): about 12 ms at p50 and p95 for a roughly 80-character message, and about 54 ms (p50) / 56 ms (p95) for roughly 800 characters. Cost grows with text length because the analyzer runs on every message. Model time and network distance are not included. Details and reproduction: [`eval/results_proxy_latency.md`](eval/results_proxy_latency.md), `python -m eval.bench_proxy_latency`.

**Claude and Gemini.** Anthropic and Google each document an OpenAI-compatible endpoint, so pointing `LLM_UPSTREAM_BASE_URL` at them should work, but that is **untested here** and both vendors label these layers a testing aid or beta (some OpenAI fields are ignored). Native Anthropic and Gemini formats are not supported. Sources and gaps: [docs/research/llm-api-formats.md](docs/research/llm-api-formats.md).

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
| `POST` | `/v1/chat/completions` | `X-API-Key` + upstream key in `Authorization` | OpenAI-compatible redacting proxy. |
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

**Limitations of this measurement:** synthetic, templated English sentences with fictional data, so real text will score lower; 24–31 examples per type is a small sample, and each type is only just past the ~20 needed to treat a per-type number as more than an anecdote; US-style phone formats only (NZ identifiers are measured separately below). The dataset was written before the first run and not changed afterwards.

### NZ identifiers

The NZ recognisers (NHI number, IRD number, driver licence) are scored on a second hand-written dataset with [`config.nz.yaml`](config/examples/config.nz.yaml), the same way. Formats and sources: [docs/research/nz-identifiers.md](docs/research/nz-identifiers.md); design: [ADR 0005](docs/adr/0005-checksum-validated-nz-recognisers.md).

| Entity | Labeled spans | False positives | Misses | Precision | Recall | F1 | Recall before |
|---|---|---|---|---|---|---|---|
| `NZ_NHI` | 27 | 0 | 0 | 1.00 | 1.00 | 1.00 | 0.00 |
| `NZ_IRD` | 26 | 0 | 0 | 1.00 | 1.00 | 1.00 | 0.00 |
| `NZ_DRIVER_LICENCE` | 26 | 4 | 0 | 0.87 | 1.00 | 0.93 | 0.00 |
| `PHONE_NUMBER` (NZ formats) | 28 | 2 | 0 | 0.93 | 1.00 | 0.97 | 1.00 |

"Recall before" is default Presidio on the same data ([`eval/results_nz_baseline.md`](eval/results_nz_baseline.md)), committed before any recogniser existed. Phone detection is Presidio's own, unchanged: it already finds these formats, and its two false alarms are IRD numbers it reads as phones (redacted either way; only the label can differ).

Dataset: 133 sentences ([`eval/dataset_nz.jsonl`](eval/dataset_nz.jsonl)), 30 of them with no NZ identifier, including look-alikes: checksum-invalid NHI and IRD numbers, IRD-shaped numbers outside the valid range, order numbers and part numbers. Reproduce with `python -m eval.run_eval --policy config/examples/config.nz.yaml --dataset eval/dataset_nz.jsonl --output eval/results_nz.md`.

**Reading these numbers:**
- NHI and IRD are validated with the issuer's published check digit, so the look-alikes are rejected. A perfect score on a dataset written by the author, who knew the algorithm, shows the code implements the published check; it does not predict 1.00 on real text.
- A valid check digit means a number is well-formed, not that it was ever issued.
- The driver licence has no published checksum, so any two capital letters followed by six digits matches. The four false alarms are part numbers of that shape, and context words ("licence", "driver") raise the score but cannot separate them.

**Limitations of this measurement:** 26–28 examples per type is a small sample, only just past the ~20 needed to call a per-type number more than an anecdote. The phone examples use only four distinct numbers in different formats, so they measure format coverage, not number variety. NHI examples all use the reserved `Z` test prefix. IRD examples mostly come from the 150M–200M range, which I believe is unissued but could not confirm, and the dashed and spaced IRD forms are assumed. Matching is upper case only. Postcodes and addresses are not detected as NZ types.

---

## Limitations

- **Best-effort redaction.** Presidio NLP produces false negatives (missed personal data) and false positives. The [Evaluation](#evaluation) numbers come from clean synthetic sentences, so they are an optimistic baseline, not a promise for your data. Do not rely on it as the only control.
- **Not a legal or compliance product.** Redacted output can still identify a person when combined with other data. Using this service does not remove your obligations under privacy law (for example the NZ Privacy Act 2020); it can help reduce exposure as one technical control. See [docs/research/nz-privacy-compliance.md](docs/research/nz-privacy-compliance.md).
- **English only.** The NLP path loads English models.
- **NZ identifiers are checked, not looked up.** A mistyped NHI or IRD number fails its check digit and is **not redacted**. Driver licence numbers have no published checksum, so look-alike codes are also redacted (precision 0.87 on the sample). A zero-padded IRD number in prose is not detected. A policy with an empty `redaction_entities` runs every recogniser, including the NZ ones.
- **LLM proxy is OpenAI-format only.** Images, tools and unknown fields are rejected, replies keep placeholders, and a missed entity reaches the upstream. See [LLM proxy](#llm-proxy-openai-compatible).
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
