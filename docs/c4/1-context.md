# C1 — System Context

**System:** PII Gateway — one self-hosted service that redacts personal data from free text and nested JSON before downstream use.

**People**

- **App integrator** — Calls `POST /v1/sanitize` with an API key.
- **Automation caller** — Hits `/internal/jobs/*` or depends on the optional in-process APScheduler.
- **Operator** — Runs Docker Compose, mounts the policy YAML/JSON, sets secrets in env.

**External systems (optional unless noted)**

- **PostgreSQL** — Named, parameterized batch SQL from the policy file only.
- **S3-compatible storage** — Inbox files and/or outbound artifacts.
- **Local volume** — Default storage backend and `GATEWAY_STATE_DIR` state files.

Presidio and spaCy run **inside** the gateway process (libraries), not as separate services.

Diagram: [1-context.mmd](1-context.mmd). Next: [2-containers](2-containers.md).
