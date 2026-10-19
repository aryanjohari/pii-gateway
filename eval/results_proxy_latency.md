# Proxy latency (fake upstream)

Run on 2026-10-19, macOS-15.5-arm64-arm-64bit, Python 3.12.13. 200 sequential requests per row after 20 warm-up requests, policy `config.nz-llm.yaml`, one user message containing a name, an NHI and a phone number. Times in milliseconds.

| Message size | Direct p50 | Direct p95 | Via gateway p50 | Via gateway p95 | Added p50 | Added p95 |
|---|---|---|---|---|---|---|
| about 80 characters | 0.7 | 0.8 | 12.4 | 13.2 | 11.7 | 12.4 |
| about 800 characters | 0.7 | 0.8 | 54.9 | 56.6 | 54.2 | 55.8 |

The upstream is a local stub that answers instantly, so this isolates the gateway's own cost. Real model time and network distance are not included and are usually far larger.
