# C4 diagrams — PII Gateway

Official-style C4 views built **bottom-up from this repo’s code**. Levels stop at **Components** (no Code / class diagrams).

## How to read (zoom path)

| Level | File | What it shows |
|-------|------|----------------|
| **C1 Context** | [1-context.mmd](1-context.mmd) · [notes](1-context.md) | People + this system as one box + external systems |
| **C2 Containers** | [2-containers.mmd](2-containers.mmd) · [notes](2-containers.md) | What actually runs / mounts / stores data |
| **C3 Components** | [3-components/pii-gateway](3-components/pii-gateway.mmd) · [notes](3-components/pii-gateway.md) | Internals of the FastAPI container |

**Zoom:** Context system box → Containers → Components (`pii-gateway` only). Machine index: [portfolio-map.json](portfolio-map.json).

Visitor narrative (premise, unique approach, tradeoffs): [../ARCHITECTURE.md](../ARCHITECTURE.md). Project card: [../../portfolio.yaml](../../portfolio.yaml).

## Portfolio

| Artifact | Role |
|----------|------|
| [portfolio-map.json](portfolio-map.json) | **Canonical** zoom index for a future Context→Containers→Components UI |
| [2-containers.mmd](2-containers.mmd) | Default Mermaid diagram linked from `portfolio.yaml` (`diagram:`) |
| [../architecture.mmd](../architecture.mmd) | Optional flowchart **alias** of C2 for renderers without Mermaid C4 |

Archived (do not use): [../archive/architecture.graph.json](../archive/architecture.graph.json).

Open Mermaid in [mermaid.live](https://mermaid.live) or [../view-architecture.html](../view-architecture.html).

## Stable IDs

Machine IDs are kebab-case (`pii-gateway`, `policy-file`, `local-volume`, `s3-compatible`). Diagram labels stay plain English.
