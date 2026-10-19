"use client";

import { useState } from "react";

export type Mode = "text" | "json";
export type DemoState = "idle" | "loading" | "success" | "error" | "offline";

type SanitizeOk = {
  ok: true;
  result: { text?: string; structured?: unknown };
  meta?: { entity_summary?: Record<string, number>; duration_ms?: number };
};

type SanitizeErr = {
  ok: false;
  error: { code: string; message: string };
  offline?: boolean;
};

export function useSanitize() {
  const [state, setState] = useState<DemoState>("idle");
  const [message, setMessage] = useState<string | null>(null);
  const [original, setOriginal] = useState<string>("");
  const [output, setOutput] = useState<string>("");
  const [summary, setSummary] = useState<Record<string, number> | null>(null);
  const [durationMs, setDurationMs] = useState<number | null>(null);

  function reset() {
    setState("idle");
    setMessage(null);
  }

  async function submit(mode: Mode, text: string, jsonText: string) {
    setState("loading");
    setMessage(null);
    setOriginal("");
    setOutput("");
    setSummary(null);
    setDurationMs(null);

    let body: { text?: string; structured?: unknown };
    if (mode === "text") {
      body = { text };
    } else {
      try {
        body = { structured: JSON.parse(jsonText) as unknown };
      } catch {
        setState("error");
        setMessage("JSON input is not valid.");
        return;
      }
    }

    try {
      const res = await fetch("/api/sanitize", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      const data = (await res.json()) as SanitizeOk | SanitizeErr;

      if (!res.ok || data.ok === false) {
        const err = data as SanitizeErr;
        if (res.status === 503 || err.offline || err.error?.code === "demo_offline") {
          setState("offline");
          setMessage(
            err.error?.message ??
              "Demo API is offline. Run the gateway with Docker Compose, or point Vercel env at your Pi tunnel.",
          );
          return;
        }
        setState("error");
        setMessage(err.error?.message ?? "Sanitize request failed.");
        return;
      }

      const ok = data as SanitizeOk;
      const pretty =
        mode === "text"
          ? String(ok.result.text ?? "")
          : JSON.stringify(ok.result.structured ?? ok.result, null, 2);
      setOriginal(mode === "text" ? text : jsonText);
      setOutput(pretty);
      setSummary(ok.meta?.entity_summary ?? null);
      setDurationMs(ok.meta?.duration_ms ?? null);
      setState("success");
    } catch {
      setState("error");
      setMessage("Could not reach the demo proxy. Check the site is running.");
    }
  }

  return { state, message, original, output, summary, durationMs, submit, reset };
}
