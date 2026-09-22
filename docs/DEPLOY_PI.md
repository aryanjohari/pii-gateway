# Deploy PII Gateway on a Raspberry Pi

Home-lab / portfolio demo path: run the same Docker image on a Pi and expose HTTPS with **Cloudflare Tunnel** (no router port-forward). The Vercel landing page stays online even if the Pi is off; flip `PII_GATEWAY_API_URL` when the tunnel is ready.

This document is a **requirements + steps checklist**. Physical setup is optional and can wait until you inventory the device.

---

## Inventory checklist

Tick what you already have before installing anything:

- [ ] Raspberry Pi **4 or 5** with **≥ 4 GB RAM** (8 GB ideal). Pi Zero / Pi 3 are too tight for Presidio + spaCy.
- [ ] **64-bit OS** (`uname -m` → `aarch64`). 32-bit images will not match `linux/arm64` containers cleanly.
- [ ] **≥ 8 GB free disk** (image layers + spaCy model + Docker overhead; 15 GB+ comfortable).
- [ ] Docker Engine + **Compose v2** (`docker compose version`).
- [ ] Stable power / cooling (Presidio can warm the SoC under load).
- [ ] Cloudflare account (free) for Tunnel **or** another HTTPS ingress you trust.
- [ ] Strong random value for `SANITIZE_HTTP_API_KEY` (and the same value in Vercel `PII_GATEWAY_API_KEY`).
- [ ] Optional: custom hostname (e.g. `api.example.com`) on the tunnel.

---

## Why these requirements

| Need | Why |
|------|-----|
| Pi 4/5, 4 GB+ RAM | AnalyzerEngine + `en_core_web_sm` are memory-heavy |
| `aarch64` | Publish/pull `linux/arm64` images (see GHCR notes in README) |
| Disk headroom | Slim Python image + spaCy model + logs |
| Docker + Compose v2 | Same primary path as local/dev |
| Gateway on `127.0.0.1:8000` only | Tunnel terminates public HTTPS; avoid opening WAN ports |
| Cloudflare Tunnel (`cloudflared`) | Works behind CGNAT/home NAT without port-forward |
| Demo policy + scheduler off | Public edge should not persist raw PII or run batch jobs |
| Vercel env → tunnel URL | Landing BFF proxies to the Pi without exposing the API key |

---

## Recommended runtime config

Use the demo policy (no artifact writes):

- Mount [`config/examples/config.demo.yaml`](../config/examples/config.demo.yaml) as `/etc/pii-gateway/config.yaml`
- Env (see [`.env.example`](../.env.example)):
  - `SANITIZE_HTTP_API_KEY` — required
  - `DISABLE_SCHEDULER=true`
  - `STORAGE_BACKEND=local`
  - `SANITIZE_RATE_LIMIT_PER_MINUTE=30` (or similar)
  - `SANITIZE_MAX_BODY_BYTES=65536`
  - `SANITIZE_MAX_CHARS=10000`
  - `CORS_ALLOWED_ORIGINS` — optional if all browser traffic goes through the Vercel BFF

Compose tips:

- `restart: unless-stopped` on the gateway service
- Publish `8000` only to localhost if possible (`127.0.0.1:8000:8000`) so only the tunnel can reach it

Example overlay idea (edit to match your paths):

```yaml
services:
  pii-gateway:
    restart: unless-stopped
    ports:
      - "127.0.0.1:8000:8000"
    volumes:
      - ./config/examples/config.demo.yaml:/etc/pii-gateway/config.yaml:ro
    environment:
      DISABLE_SCHEDULER: "true"
      SANITIZE_RATE_LIMIT_PER_MINUTE: "30"
```

---

## Cloudflare Tunnel (preferred public HTTPS)

1. Install `cloudflared` on the Pi ([Cloudflare docs](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/)).
2. Authenticate and create a tunnel.
3. Route a public hostname to `http://127.0.0.1:8000`.
4. Confirm `GET https://<your-host>/healthz` returns `{"status":"ok"}`.
5. Confirm `POST /v1/sanitize` with `X-API-Key` works (sample data only).

**Do not** rely on raw WAN port-forwarding for a home demo if a tunnel is available.

---

## Point the Vercel playground at the Pi

In the Vercel project for [`web/`](../web/):

| Secret | Value |
|--------|--------|
| `PII_GATEWAY_API_URL` | `https://<tunnel-hostname>` (no trailing slash) |
| `PII_GATEWAY_API_KEY` | Same as Pi `SANITIZE_HTTP_API_KEY` |

Redeploy or refresh env. The landing site itself stays on Vercel; only the sanitize BFF calls the Pi.

If the Pi or tunnel is down, the playground shows an **offline** state and still links to self-host instructions—that is expected.

---

## Image architecture

Prefer pulling a published multi-arch image (`linux/amd64` + `linux/arm64`) from GHCR when available:

```bash
docker pull ghcr.io/aryanjohari/pii-gateway:latest
```

Or build on the Pi from this repo (`docker compose build`)—slower, but works offline from registries.

---

## Smoke test

```bash
curl -sS http://127.0.0.1:8000/healthz
curl -sS -X POST http://127.0.0.1:8000/v1/sanitize \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $SANITIZE_HTTP_API_KEY" \
  -d '{"text":"Contact alice@example.com"}'
```

Then the same against the tunnel URL.

---

## Operational expectations

- Home uptime is **not** an SLA—say so on the landing page / README.
- NLP on a Pi is slower than a laptop/cloud CPU; timeouts on the BFF may need patience.
- Never send real personal data to a public demo endpoint.
- Tear down or stop Compose when you do not need the demo to save power.

---

## Related

- Web app setup: [`web/README.md`](../web/README.md)
- Local Compose: root [`README.md`](../README.md)
- Demo policy: [`config/examples/config.demo.yaml`](../config/examples/config.demo.yaml) — after `git pull`, remount/restart so the container sees the updated file.
