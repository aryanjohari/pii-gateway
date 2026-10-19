// Mirrors `sanitize_max_chars` in src/pii_gateway/settings.py (also set in docker-compose.demo.yml).
// Keep the three in step. The gateway is the source of truth and answers 413 when exceeded.
export const MAX_INPUT_CHARS = 10_000;
