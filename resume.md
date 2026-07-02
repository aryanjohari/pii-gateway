# PII Gateway

Ground-truth evidence for CV bullets and cover letters. Fill in every section with verified facts only.

## One-line summary

Self-hosted PII sanitization gateway (FastAPI + Microsoft Presidio) that redacts free text and structured JSON via a mounted policy file, with optional batch ingestion from PostgreSQL, CSV/JSON-array files, and S3-compatible storage.

## Context

- **Role:** Solo developer [inferred from codebase — sole git author `aryanjohari`, 5 commits]
- **Dates:** Mar 2026 -- May 2026 [inferred from git: initial commit 2026-03-22, latest 2026-05-06]
- **Institution / org:** N/A — described in `PROJECT.md` as a personal / learning project
- **Links:** https://github.com/aryanjohari/pii-gateway

## Problem

Applications and pipelines often need to pass data to analytics, logging, or LLM tools without exposing raw personally identifiable information. This project provides a single Docker-first service that applies NLP-based entity detection (Presidio) and config-driven field rules to sanitize payloads before they reach downstream systems. It supports real-time HTTP JSON requests and optional scheduled batch exports from PostgreSQL or file inboxes. The README and architecture docs state it is not a safe OLTP database proxy or a substitute for a full compliance program.

## Your contributions

- Designed and implemented the full codebase as sole author (all 5 git commits attributed to `aryanjohari`) [inferred from git history]
- Built FastAPI application entrypoint with lifespan hooks that instantiate Presidio `AnalyzerEngine` and `AnonymizerEngine` once per process (`src/pii_gateway/main.py`)
- Implemented `POST /v1/sanitize` real-time API with `X-API-Key` authentication, Pydantic v2 request/response schemas, and structured error responses (`src/pii_gateway/api/`)
- Built sanitization pipeline combining free-text Presidio redaction and structured JSON field handling (`redact`, `tokenize`, `mask`, `passthrough`) via `src/pii_gateway/core/sanitize_pipeline.py` and helpers
- Defined policy schema and YAML/JSON config loader for entity allowlists, structured field rules, Postgres batch queries, file inbox settings, and persistence flags (`src/pii_gateway/policy_schema.py`, `src/pii_gateway/config_loader.py`)
- Implemented outbound storage abstraction with local filesystem and S3-compatible backends using `aioboto3` (`src/pii_gateway/storage/`)
- Built batch inbound connectors: PostgreSQL streaming via SQLAlchemy async + `asyncpg`, CSV via pandas, JSON-array files, and S3-compatible inbox listing (`src/pii_gateway/connectors/`, `src/pii_gateway/jobs/`)
- Added internal job routes (`POST /internal/jobs/postgres-batch`, `POST /internal/jobs/file-ingest`) gated by `X-Internal-Job-Key`, plus APScheduler for recurring batch work (`src/pii_gateway/jobs/scheduler.py`)
- Implemented correlation-ID middleware, optional CORS, structured logging without raw payload leakage, and state store for batch cursors (`src/pii_gateway/api/middleware.py`, `src/pii_gateway/logging_config.py`, `src/pii_gateway/state_store.py`)
- Packaged as Docker image with healthcheck and `docker-compose.yml`; optional `docker-compose.example.yml` overlay for Postgres + MinIO + gateway
- Added GitHub Actions CI running ruff, mypy, pytest on Python 3.11 and 3.12, plus Docker build on 3.12 (`.github/workflows/ci.yml`)
- Wrote unit and integration test suite (33 test functions across 14 test modules) covering auth, sanitization, batch helpers, storage factory, and HTTP API behavior via Starlette `TestClient`
- Authored operator documentation (`README.md`), project narrative (`PROJECT.md`), architecture diagram (`docs/architecture.mmd`), and contributing guidelines (`CONTRIBUTING.md`)
- Commit message on 2026-04-30 references "final PoC" [VERIFY whether you still describe this as PoC vs beta — tag `v1.0-beta` also appears in git]

## Tech stack

Python 3.11+, FastAPI, Uvicorn, Pydantic v2, pydantic-settings, Microsoft Presidio (presidio-analyzer, presidio-anonymizer), spaCy (`en_core_web_sm`), SQLAlchemy 2 (async), asyncpg, pandas, APScheduler, aioboto3, PyYAML, pytest, pytest-asyncio, pytest-cov, httpx, ruff, mypy, Docker, Docker Compose, GitHub Actions

## Architecture (optional but helpful)

Single-container FastAPI service. On startup: load env settings (`pydantic-settings`) and mounted policy file (`PII_GATEWAY_CONFIG_PATH`), create Presidio singletons, select outbound storage backend, optionally open async Postgres engine and APScheduler.

**Inbound paths:** (1) `POST /v1/sanitize` for real-time JSON with optional `text` and `structured` fields; (2) scheduled or manually triggered Postgres batch via named parameterized SQL in policy; (3) file inbox polling for `.csv` and root-level JSON arrays from local directory or S3-compatible bucket.

**Core:** `sanitize_payload` runs Presidio analysis on text and nested string values, applies `structured_field_rules`, returns sanitized result plus entity-type counts (no raw PII in metadata).

**Outbound:** Optional `raw` / `cleaned` artifact writes through `OutboundStorage` protocol to local volume or S3-compatible bucket; paths include date partitioning and source labels.

**Key directories:** `src/pii_gateway/api/` (HTTP layer), `core/` (sanitization), `connectors/` (batch ingest), `jobs/` (scheduler + batch jobs), `storage/` (backends), `tests/unit/` and `tests/integration/`.

## Outcomes & metrics (verified only)

| Metric | Value | How measured | Notes |
|--------|-------|--------------|-------|
| HTTP API endpoints | 4 | `README.md` reference table + `main.py` | `/v1/sanitize`, `/healthz`, `/internal/jobs/postgres-batch`, `/internal/jobs/file-ingest` |
| Python source modules | 33 | `src/pii_gateway/**/*.py` file count | |
| Python source lines | ~1,560 | `wc -l` on `src/pii_gateway/**/*.py` | Approximate |
| Test functions | 33 | `grep` for `def test_` / `async def test_` in `tests/` | 11 unit modules + 3 integration modules |
| Test + source lines (combined) | ~2,113 | `wc -l` on src + tests Python files | Approximate |
| Package version | 0.1.0 | `pyproject.toml` | Commit message also references `v1.0-beta` |
| CI Python versions | 3.11, 3.12 | `.github/workflows/ci.yml` matrix | |
| Presidio language | English (`language="en"`) | `sanitize_pipeline.py` | Other languages not implemented |
| Production users / traffic | not recorded | | |
| Test coverage threshold | none enforced | `pyproject.toml` `cov-fail-under=0` | Coverage reported but no minimum set |
| Benchmark latency / throughput | not recorded | | `duration_ms` returned per request in API meta only |

## Keywords for tailoring

PII redaction, data sanitization, FastAPI, Presidio, NLP entity detection, Docker, microservice, API gateway, Pydantic, async Python, PostgreSQL batch, S3-compatible storage, MinIO, pandas, SQLAlchemy, pytest, GitHub Actions, 12-factor config, privacy engineering, structured logging

## Do not claim

- Production deployment or real user traffic (not recorded in repo)
- Enterprise clients or commercial adoption
- Team leadership or multi-contributor development (sole author in git)
- Compliance certification, DLP replacement, or database firewall capabilities (explicitly disclaimed in README and `PROJECT.md`)
- External security audit or penetration test (`PROJECT.md` states none)
- Published container registry image (listed as future roadmap in `PROJECT.md`; CI builds image but does not publish)
- Full real-world validation of all batch/S3/Postgres paths (`PROJECT.md`: "Havent currently real-world tested all options")
- Multi-language PII detection (code hardcodes English)
- Hosted multi-tenant SaaS (explicit non-goal in `architecture.plan.md`)
- DynamoDB or other NoSQL inbound connectors (explicitly out of scope)
- HTTPS termination inside the app (TLS expected at edge proxy per README)

## Suggested CV tags

`backend`, `python`, `fastapi`, `docker`, `privacy`, `api`

## Open questions for Aryan

- Confirm project status label: PoC (per 2026-04-30 commit), beta (`v1.0-beta` commit), or active side project?
- Has this been deployed anywhere beyond local Docker Compose (e.g. cloud VM, ECS, Kubernetes)? If yes, where and when?
- Is this affiliated with coursework, an employer, or purely personal? `PROJECT.md` says personal — confirm for CV context.
- Any real-world usage metrics (requests processed, datasets sanitized) you want recorded?
- Do you want dates shown as Mar 2026 -- May 2026, or is development ongoing past May 2026?
- Was spaCy `en_core_web_sm` model choice and English-only scope intentional for portfolio positioning, or planned for expansion?
