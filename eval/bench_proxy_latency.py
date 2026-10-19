"""Measure the latency the chat proxy adds, against a local fake upstream.

Starts a stub upstream and the gateway (real sockets, one process), then times
sequential requests through the gateway and straight to the stub. The difference is
the cost of validation, redaction and the extra hop. It excludes network distance
and model time, which dominate in real use.

    python -m eval.bench_proxy_latency
"""

import argparse
import json
import os
import platform
import subprocess
import sys
import tempfile
import threading
import time
from datetime import date
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "config" / "examples" / "config.nz-llm.yaml"
SENTENCE = "Patient Jane Smith (NHI ZAC5361) rang from 021 123 4567 about her results. "
REPLY = json.dumps({"id": "x", "object": "chat.completion", "choices": []}).encode()


class _Stub(BaseHTTPRequestHandler):
    def do_POST(self) -> None:
        self.rfile.read(int(self.headers["Content-Length"]))
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(REPLY)))
        self.end_headers()
        self.wfile.write(REPLY)

    def log_message(self, *args: object) -> None:
        pass


def _percentile(sorted_ms: list[float], fraction: float) -> float:
    return sorted_ms[min(len(sorted_ms) - 1, int(fraction * len(sorted_ms)))]


def _time_requests(
    client: httpx.Client, url: str, body: dict[str, object], count: int
) -> list[float]:
    headers = {"X-API-Key": "bench", "Authorization": "Bearer sk-bench"}
    for _ in range(20):  # warm-up: model load, connection setup
        client.post(url, json=body, headers=headers).raise_for_status()
    timings: list[float] = []
    for _ in range(count):
        start = time.perf_counter()
        client.post(url, json=body, headers=headers).raise_for_status()
        timings.append((time.perf_counter() - start) * 1000)
    return sorted(timings)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--requests", type=int, default=200)
    parser.add_argument("--output", type=Path, default=ROOT / "eval" / "results_proxy_latency.md")
    args = parser.parse_args()

    stub = ThreadingHTTPServer(("127.0.0.1", 9102), _Stub)
    threading.Thread(target=stub.serve_forever, daemon=True).start()
    scratch = tempfile.mkdtemp()
    env = {
        **os.environ,
        "SANITIZE_HTTP_API_KEY": "bench",
        "LLM_UPSTREAM_BASE_URL": "http://127.0.0.1:9102/v1",
        "PII_GATEWAY_CONFIG_PATH": str(POLICY),
        "STORAGE_LOCAL_PATH": scratch,
        "GATEWAY_STATE_DIR": scratch,
        "DISABLE_SCHEDULER": "true",
        "SANITIZE_RATE_LIMIT_PER_MINUTE": "0",
        "SANITIZE_MAX_CHARS": "0",
        "SANITIZE_MAX_BODY_BYTES": "0",
    }
    gateway = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "pii_gateway.main:app", "--port", "8011"],
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    rows: list[str] = []
    try:
        with httpx.Client(timeout=30) as client:
            for _ in range(120):
                try:
                    client.get("http://127.0.0.1:8011/healthz").raise_for_status()
                    break
                except httpx.HTTPError:
                    time.sleep(0.5)
            for label, repeats in (("about 80 characters", 1), ("about 800 characters", 10)):
                body = {
                    "model": "m",
                    "messages": [{"role": "user", "content": SENTENCE * repeats}],
                }
                direct = _time_requests(
                    client, "http://127.0.0.1:9102/v1/chat/completions", body, args.requests
                )
                proxied = _time_requests(
                    client, "http://127.0.0.1:8011/v1/chat/completions", body, args.requests
                )
                rows.append(
                    f"| {label} | {_percentile(direct, 0.5):.1f} | {_percentile(direct, 0.95):.1f} "
                    f"| {_percentile(proxied, 0.5):.1f} | {_percentile(proxied, 0.95):.1f} "
                    f"| {_percentile(proxied, 0.5) - _percentile(direct, 0.5):.1f} "
                    f"| {_percentile(proxied, 0.95) - _percentile(direct, 0.95):.1f} |"
                )
    finally:
        gateway.terminate()
        gateway.wait(timeout=10)
        stub.shutdown()

    args.output.write_text(
        "# Proxy latency (fake upstream)\n\n"
        f"Run on {date.today().isoformat()}, {platform.platform()}, "
        f"Python {platform.python_version()}. "
        f"{args.requests} sequential requests per row after 20 warm-up requests, policy "
        "`config.nz-llm.yaml`, one user message containing a name, an NHI and a phone number. "
        "Times in milliseconds.\n\n"
        "| Message size | Direct p50 | Direct p95 | Via gateway p50 | Via gateway p95 "
        "| Added p50 | Added p95 |\n|---|---|---|---|---|---|---|\n" + "\n".join(rows) + "\n\n"
        "The upstream is a local stub that answers instantly, so this isolates the gateway's own "
        "cost. Real model time and network distance are not included and are usually far larger.\n",
        encoding="utf-8",
    )
    print(args.output.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
