# ADR 0001: Docker-first single-tenant service instead of Lambda/DynamoDB SaaS

- Status: Accepted (recorded retroactively on 2026-10-19; the decision predates this file)
- Note: the reasons below are what the current code depends on. The original discussion lived in an early plan document that is no longer tracked, so treat the history as summarised, not quoted.

## Context
Early plans targeted a multi-tenant serverless SaaS (Lambda and DynamoDB). The shipped service is different in ways that matter for hosting:
- Presidio's `AnalyzerEngine` loads an NLP model and is built once per process in the FastAPI lifespan (`main.py`). Per-invocation startup would pay that cost repeatedly.
- Batch jobs keep state on disk (`postgres_batch_cursor.json`, `processed_files.json` under `GATEWAY_STATE_DIR`) and run on an in-process APScheduler.
- The audience is someone self-hosting a demo or a small internal tool, including on a Raspberry Pi (`docs/DEPLOY_PI.md`, multi-arch image).

## Decision
Ship one container (`Dockerfile`, `docker-compose.yml`). Config comes from environment variables plus a mounted policy file. Storage is a local volume or any S3-compatible endpoint (MinIO, R2, AWS S3), never an AWS-only SDK path. The service is single-tenant.

## Consequences
- Easy to run anywhere with `docker compose up`; one process holds the model, scheduler and HTTP API.
- Scaling out is not free: several replicas would each run the scheduler and keep their own state files, so duplicate runs are possible. Run one replica, or disable the scheduler (`DISABLE_SCHEDULER`) and trigger `/internal/jobs/*` from an external cron.
- No tenant isolation, billing or per-customer quotas. A hosted SaaS would need a different design.

## Alternatives considered
- **Lambda + DynamoDB:** rejected for the model load cost and the file-based state above, and because it ties the project to one cloud.
