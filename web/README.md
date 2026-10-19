# PII Gateway web (landing + playground)

Next.js product page for [pii-gateway](https://github.com/aryanjohari/pii-gateway). The browser never sees the gateway API key—`/api/sanitize` proxies server-side.

## Local development

1. Start the gateway:

```bash
cd ..
cp .env.example .env
# set SANITIZE_HTTP_API_KEY
docker compose up --build
```

2. Configure the web app:

```bash
cd web
cp .env.example .env.local
# PII_GATEWAY_API_URL=http://127.0.0.1:8000
# PII_GATEWAY_API_KEY=<same key>
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000). If env vars are missing, the playground shows an offline state with a self-host CTA.

The playground is **policy-first**: declared JSON fields get deterministic placeholders; free-text NLP is best-effort. Sample data only—not a compliance product.

## Checks

```bash
npm run lint        # ESLint with jsx-a11y
npm run typecheck
npm test            # unit and component tests (vitest, Testing Library)
npm run build && npx playwright install chromium && npm run e2e   # browser flows with axe
```

Automated accessibility checks find only part of the problems. A clean axe run is not proof of accessibility; a screen-reader pass is still a manual check.

## Vercel

1. Import this `web/` directory as the project root (or set Root Directory to `web`).
2. Set secrets: `PII_GATEWAY_API_URL`, `PII_GATEWAY_API_KEY`.
3. Deploy. When your Raspberry Pi tunnel is ready, update `PII_GATEWAY_API_URL` to the tunnel URL (see [docs/DEPLOY_PI.md](../docs/DEPLOY_PI.md)).

Do not put real PII in the public demo. After pulling gateway policy changes, remount/restart the Pi container with the updated [`config.demo-nz.yaml`](../config/examples/config.demo-nz.yaml).
