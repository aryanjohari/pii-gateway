# C4 diagrams — PII Gateway

C4 views of this repository, grounded in the running code (FastAPI entrypoint, Compose, routes, jobs, storage). There is **no Code-level** diagram.

## How to read

| Level | File | What it shows |
|-------|------|----------------|
| **C1 Context** | [1-context.mmd](1-context.mmd) · [notes](1-context.md) | People + this system as one box + external systems |
| **C2 Containers** | [2-containers.mmd](2-containers.mmd) · [notes](2-containers.md) | Deployable pieces and data stores — **default portfolio map** |
| **C3 Components** | [3-components/](3-components/) | Internals of containers that need a zoom |

Start at C1 for orientation, use C2 for “what runs where,” open C3 only when you need API internals.

Visitor-facing narrative: [../ARCHITECTURE.md](../ARCHITECTURE.md). Project card: [../../portfolio.yaml](../../portfolio.yaml).

## Portfolio / graph

| Artifact | Role |
|----------|------|
| [../architecture.graph.json](../architecture.graph.json) | Preferred map IR for aryan-portfolio (`graph:` in `portfolio.yaml`) |
| [../architecture.mmd](../architecture.mmd) | Visitor Mermaid fallback (`diagram:` in `portfolio.yaml`) |
| [portfolio-map.json](portfolio-map.json) | Which container IDs have C3 component diagrams |

Open Mermaid sources in [mermaid.live](https://mermaid.live) or [../view-architecture.html](../view-architecture.html) (loads `architecture.mmd`).

## Stable IDs

Machine IDs use kebab-case (`pii-gateway`, `policy-file`, `s3-compatible`). Diagram labels stay plain English for GitHub visitors and interviewers.
