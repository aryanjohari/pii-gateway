"use client";

import { useState } from "react";

import { MAX_INPUT_CHARS } from "@/lib/limits";
import { parseSanitizeResponse } from "@/lib/sanitizeResponse";

export type Mode = "text" | "json";
export type DemoState = "idle" | "loading" | "success" | "error";
export type ProblemKind =
  | "empty"
  | "too_long"
  | "invalid_json"
  | "rate_limited"
  | "offline"
  | "unexpected";

export type Problem = { kind: ProblemKind; message: string };

const LIMIT_LABEL = MAX_INPUT_CHARS.toLocaleString("en-NZ");

// Our own wording by kind. Upstream error bodies are never shown (they can echo the input).
const MESSAGES = {
  empty: "Add some text first, or pick a sample above.",
  invalid_json: "That is not valid JSON. Fix the syntax, or pick a sample above.",
  json_not_object: 'The JSON must be an object like {"field": "value"}, not a list or a single value.',
  rate_limited:
    "Too many requests from this address. Wait a minute and try again, or self-host.",
  offline: "The public demo is offline. This does not affect self-hosted copies.",
  unexpected: "Something went wrong. Try again in a moment.",
};

function tooLong(length: number | null): Problem {
  const message =
    length == null
      ? `That input is over the demo's ${LIMIT_LABEL} character limit. Shorten it, or self-host.`
      : `That is ${length.toLocaleString("en-NZ")} characters; the demo accepts up to ${LIMIT_LABEL}. Shorten the text, or self-host.`;
  return { kind: "too_long", message };
}

function problemFor(status: number, code: string | null, offline: boolean): Problem {
  if (status === 429 || code === "rate_limited") {
    return { kind: "rate_limited", message: MESSAGES.rate_limited };
  }
  if (status === 413 || code === "payload_too_large") return tooLong(null);
  if (status === 503 || offline || code === "demo_offline") {
    return { kind: "offline", message: MESSAGES.offline };
  }
  return { kind: "unexpected", message: MESSAGES.unexpected };
}

export function useSanitize() {
  const [state, setState] = useState<DemoState>("idle");
  const [problem, setProblem] = useState<Problem | null>(null);
  const [submittedMode, setSubmittedMode] = useState<Mode>("text");
  const [original, setOriginal] = useState<string>("");
  const [output, setOutput] = useState<string>("");
  const [summary, setSummary] = useState<Record<string, number> | null>(null);
  const [durationMs, setDurationMs] = useState<number | null>(null);

  function reset() {
    setState("idle");
    setProblem(null);
  }

  function fail(next: Problem) {
    setState("error");
    setProblem(next);
  }

  async function submit(mode: Mode, text: string, jsonText: string) {
    setProblem(null);
    setOriginal("");
    setOutput("");
    setSummary(null);
    setDurationMs(null);

    const input = mode === "text" ? text : jsonText;
    if (input.trim().length === 0) {
      fail({ kind: "empty", message: MESSAGES.empty });
      return;
    }
    if (mode === "text" && text.length > MAX_INPUT_CHARS) {
      fail(tooLong(text.length));
      return;
    }

    let body: { text?: string; structured?: unknown };
    if (mode === "text") {
      body = { text };
    } else {
      let structured: unknown;
      try {
        structured = JSON.parse(jsonText);
      } catch {
        fail({ kind: "invalid_json", message: MESSAGES.invalid_json });
        return;
      }
      // The gateway accepts an object only; say so here instead of showing a generic failure.
      if (typeof structured !== "object" || structured === null || Array.isArray(structured)) {
        fail({ kind: "invalid_json", message: MESSAGES.json_not_object });
        return;
      }
      body = { structured };
    }

    setState("loading");
    try {
      const res = await fetch("/api/sanitize", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      const data: unknown = await res.json().catch(() => null);
      const parsed = parseSanitizeResponse(data);

      if (!res.ok || parsed.kind !== "ok") {
        const offline = data !== null && typeof data === "object" && "offline" in data;
        fail(problemFor(res.status, parsed.kind === "error" ? parsed.code : null, offline));
        return;
      }

      const { value } = parsed;
      setSubmittedMode(mode);
      setOriginal(input);
      setOutput(
        mode === "text"
          ? (value.text ?? "")
          : JSON.stringify(value.structured ?? {}, null, 2),
      );
      setSummary(value.entitySummary);
      setDurationMs(value.durationMs);
      setState("success");
    } catch {
      fail({ kind: "unexpected", message: MESSAGES.unexpected });
    }
  }

  return { state, problem, submittedMode, original, output, summary, durationMs, submit, reset };
}
