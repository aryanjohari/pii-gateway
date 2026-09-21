# PII Gateway

> **One-line:** A Docker-friendly **Presidio + FastAPI** service that scrubs **plain text** and **nested JSON** from a mounted **policy file**, with optional **batch/file ingestion** and **artifact storage**. It centralizes redaction; it is **not** a compliance program or database firewall (personal / learning project).

Visitor card copy lives in [`portfolio.yaml`](portfolio.yaml). Design deep-dive: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md). Canonical C4: [`docs/c4/`](docs/c4/) · [`docs/c4/portfolio-map.json`](docs/c4/portfolio-map.json).

---

## What problem this solves

You want a **single service** between messy sources and downstream tools that should not see raw PII (analytics, uncertain logging, LLM experiments). Callers send HTTP JSON, or configured jobs pull Postgres exports / CSV·JSON inboxes; the gateway returns cleaned data and can write optional artifacts to local disk or S3-compatible storage.

Batch SQL must be **reviewed, parameterized, and read-only**—this is not a safe OLTP proxy.

---

## How it works (short)

1. **Startup** — Env settings + mounted policy; build Presidio analyzer/anonymizer **once**; pick storage; optional Postgres engine + APScheduler.
2. **Realtime** — `POST /v1/sanitize` with `X-API-Key`; free text + nested `structured` JSON through the same pipeline (per-field rules, fail-closed NLP on undeclared strings).
3. **Batch / files** — `/internal/jobs/*` (or scheduler) for named Postgres queries and inbox scans.

For components, data flow, unique design choices, and limitations, read **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)**. C4 levels: [docs/c4/README.md](docs/c4/README.md). Optional flowchart viewer: [docs/view-architecture.html](docs/view-architecture.html).

---

## Current state

- Compose + `/healthz` + authenticated `/v1/sanitize` work as documented in the [README](README.md)
- Public edge limits: per-IP rate limit + body/character caps (see env in [`.env.example`](.env.example))
- Product landing + playground: [`web/`](web/) (configure `PII_GATEWAY_API_*`; offline UX if unset)
- Home-lab demo host checklist (Pi + tunnel): [docs/DEPLOY_PI.md](docs/DEPLOY_PI.md) — physical setup optional
- Internal batch/file triggers and S3 paths are implemented; not all options are real-world hardened—expect gaps on less-tested connectors
- **English-only** Presidio language path; NLP false positives/negatives are normal
- **License:** MIT — [LICENSE](LICENSE)
- **Repo:** https://github.com/aryanjohari/pii-gateway

Run and integrate: [README.md](README.md). Contribute: [CONTRIBUTING.md](CONTRIBUTING.md).
