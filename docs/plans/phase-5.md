# Plan: Phase 5, finish, ship and tell the story

Goal: close the audit items deliberately left out of earlier phases, cut a real release, and turn the project into evidence a reader can check in five minutes. No new product features.
Size: medium (about 1 to 1.5 weeks, mostly small diffs and writing). Branch per part: `phase-5a-hardening`, `phase-5b-story`. One commit per step; stop for approval after each.
State at planning time (checked): no git tags, no `.pre-commit-config.yaml`, no Python lockfile, CI does not touch `web/`, no screenshot or GIF in the repo, `rate_limit.py` keys on the direct client host, `LEARNING.md` is 53 lines.

## Part A: hardening (the "out of scope until planned" list)

| Step | Change | Done when |
|---|---|---|
| 5.1 | **Rate-limit client IP behind a proxy.** Read the real client from a trusted header only when a setting names one (for example `TRUSTED_PROXY_HEADER=CF-Connecting-IP`); default stays the direct host. Never trust the header by default (spoofing). | tests: header ignored when the setting is empty; used when set; bucket separation per client |
| 5.2 | **Pre-commit** with ruff (lint + format check). Document `pre-commit install` in CONTRIBUTING. Needs approval: it is a new dev tool, not a runtime dependency. | a bad commit is blocked locally; CI unchanged |
| 5.3 | **Reproducible installs.** Choose one approach with your approval (a `constraints.txt` generated from a clean install, or `uv.lock`) and use it in the Dockerfile and CI. Recommendation: constraints file, least tooling. | `docker build` and CI install the pinned versions; update steps documented |
| 5.4 | **CI for `web/`:** `npm ci`, lint, `next build`. Path-filtered so Python-only changes skip it. | CI green; fails on a deliberate type error in a throwaway branch |
| 5.5 | **Dedupe `jobs/file_ingest.py`** only if the audit still flags it after the tests from Phase 1. Behaviour-preserving, protected by the existing tests. Skip and record as a limit if it isn't clearly worth it. | tests unchanged and green; function sizes reduced |

Skills: `/test-gap` after 5.1, `/scope-check` before the PR, `/phase-close` for Part A.

## Part B: story and evidence

| Step | Change | Done when |
|---|---|---|
| 5.6 | **Release v0.1.0.** Tag and publish the GHCR image. **Needs explicit approval for the tag; it triggers a public publish.** Verify `docker pull` and the quick start on a clean checkout. | image pulls; README quick start works unmodified |
| 5.7 | **Dogfood and record.** Use the proxy in one of your own projects for a week. Keep a short log: requests, entity counts by type, latency added, bugs found. No message content in the log. | `docs/dogfooding.md` with real counts, the bugs found, and what changed because of them |
| 5.8 | **Demo asset:** a short GIF or screenshots of the playground and a proxy before/after. Real output, not mocked. | embedded near the top of the README |
| 5.9 | **Honest status block** at the top of the README: portfolio project, used in own projects, synthetic and author-written eval data, not a compliance product, no external users yet. | block present; no "compliant" or "anonymised" anywhere (`grep`) |
| 5.10 | **Case study** with `/case-study`: problem, approach, key decisions and tradeoffs (link the ADRs), results (baseline to improved, with sample sizes), dogfooding findings, what you would do differently. | file in `docs/` or portfolio entry; every number traces to a committed file |
| 5.11 | **Final `/repo-audit`** and compare to the first (B+). Record the new grades in the case study. | audit saved; remaining gaps listed honestly |

## Honest-reporting rules
- Evidence from your own projects is "used in my own projects", not adoption.
- Numbers in the case study must be reproducible from a command in the repo, or labelled as a single run.
- Say what the eval cannot show: the data is synthetic and written by the same person who wrote the recognisers.

## Out of scope
New recognisers or providers, response restoration, streaming (unless already shipped), browser extension, CLI, hosted service, marketing, seeking outside users.

## Questions to settle first
- Is there a project of yours that will really use the proxy within the next two weeks? If not, 5.7 becomes "run a scripted realistic workload", and the doc must say so.
- Constraints file or `uv.lock` (5.3)?
- Do you want a short written test of the proxy by someone else (a friend sends it 20 realistic prompts) to reduce the author-written-data problem? Cheap and valuable.

## Learning checkpoint (`docs/LEARNING.md`)
In your own words: why header trust must be opt-in (spoofing), what a lockfile protects against, and the three weakest points of your own evaluation, which are the questions an interviewer will ask.
