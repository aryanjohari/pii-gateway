"use client";

import { useMemo, useState, type FormEvent, type ReactNode } from "react";

import { BeforeAfter } from "./BeforeAfter";
import { useSanitize, type Mode } from "./useSanitize";

const TEXT_SAMPLE =
  "Please email alice@example.com about the invoice.";
const JSON_SAMPLE = `{
  "email": "bob@example.com",
  "full_name": "Bob Smith",
  "note": "Follow up with alice@example.com"
}`;

export function Playground() {
  const [mode, setMode] = useState<Mode>("text");
  const [text, setText] = useState(TEXT_SAMPLE);
  const [jsonText, setJsonText] = useState(JSON_SAMPLE);
  const { state, message, original, output, summary, durationMs, submit, reset } = useSanitize();

  const canSubmit = useMemo(() => {
    if (state === "loading") return false;
    if (mode === "text") return text.trim().length > 0;
    return jsonText.trim().length > 0;
  }, [mode, text, jsonText, state]);

  function onSubmit(event: FormEvent) {
    event.preventDefault();
    void submit(mode, text, jsonText);
  }

  function loadSample(kind: "email" | "name") {
    if (kind === "email") {
      setMode("text");
      setText("Contact alice@example.com for details.");
    } else {
      setMode("json");
      setJsonText(JSON_SAMPLE);
    }
    reset();
  }

  return (
    <section id="demo" className="animate-rise scroll-mt-8" style={{ animationDelay: "80ms" }}>
      <div className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h2 className="font-display text-3xl font-bold tracking-tight text-ink sm:text-4xl">
            Live demo
          </h2>
          <p className="mt-2 max-w-xl text-muted">
            Paste sample text or JSON. Declared JSON fields follow policy rules;
            free-text NLP is best-effort. API keys stay server-side.
          </p>
        </div>
        <p className="text-sm text-muted">Sample data only — not for real PII.</p>
      </div>
      <p className="mb-4 max-w-2xl text-sm leading-relaxed text-muted">
        Policy-first demo: not a compliance product. Names in free text may only
        partially redact. For batch exports, prefer declared field rules over NLP
        alone.
      </p>

      <form
        onSubmit={onSubmit}
        className="overflow-hidden rounded-2xl border border-line bg-white/70 shadow-soft backdrop-blur"
      >
        <div className="flex flex-wrap items-center gap-2 border-b border-line px-4 py-3">
          <ModeButton active={mode === "text"} onClick={() => setMode("text")}>
            Text
          </ModeButton>
          <ModeButton active={mode === "json"} onClick={() => setMode("json")}>
            JSON
          </ModeButton>
          <div className="ml-auto flex gap-2">
            <SampleChip onClick={() => loadSample("email")}>Email sample</SampleChip>
            <SampleChip onClick={() => loadSample("name")}>Name + JSON sample</SampleChip>
          </div>
        </div>

        <label className="block p-4">
          <span className="mb-2 block text-xs font-medium uppercase tracking-wider text-muted">
            Input
          </span>
          <textarea
            value={mode === "text" ? text : jsonText}
            onChange={(e) =>
              mode === "text" ? setText(e.target.value) : setJsonText(e.target.value)
            }
            rows={8}
            spellCheck={mode === "text"}
            className="w-full resize-y rounded-xl border border-muted bg-mist/50 p-3 font-mono text-sm leading-relaxed text-ink focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent"
          />
        </label>

        <div className="border-t border-line px-4 py-3 text-sm">
          <div role="status" className="text-ink">
            {state === "idle" && <p className="text-muted">Redacted result appears below.</p>}
            {state === "loading" && <p className="text-muted">Sanitizing…</p>}
            {state === "success" && (
              <p>
                Done.{" "}
                {summary && Object.keys(summary).length > 0
                  ? `Removed ${Object.entries(summary)
                      .map(([entity, count]) => `${entity}: ${count}`)
                      .join(", ")}.`
                  : "Nothing was detected."}
              </p>
            )}
            {(state === "error" || state === "offline") && (
              <p className={state === "offline" ? "text-accent" : "text-red-800"}>{message}</p>
            )}
          </div>

          {state === "success" && durationMs != null && (
            <p className="mt-1 text-xs text-muted">{durationMs} ms</p>
          )}

          {state === "offline" && (
            <a
              href="#self-host"
              className="mt-3 inline-block text-sm font-medium text-accent underline-offset-4 hover:underline"
            >
              See self-host instructions
            </a>
          )}
        </div>

        <div className="flex items-center justify-between gap-3 border-t border-line px-4 py-3">
          <p className="text-xs text-muted">
            Rate-limited public edge. Prefer Compose for real workloads.
          </p>
          <button
            type="submit"
            disabled={!canSubmit}
            className="rounded-full bg-ink px-5 py-2.5 text-sm font-medium text-paper transition enabled:hover:bg-accent disabled:cursor-not-allowed disabled:opacity-40"
          >
            {state === "loading" ? "Working…" : "Sanitize"}
          </button>
        </div>

        {state === "success" && (
          <div className="animate-fade">
            <BeforeAfter mode={mode} original={original} redacted={output} />
          </div>
        )}
      </form>
    </section>
  );
}

function ModeButton({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: ReactNode;
}) {
  return (
    <button
      type="button"
      aria-pressed={active}
      onClick={onClick}
      className={`rounded-full px-3 py-1.5 text-sm transition ${
        active ? "bg-ink text-paper" : "text-muted hover:text-ink"
      }`}
    >
      {children}
    </button>
  );
}

function SampleChip({
  onClick,
  children,
}: {
  onClick: () => void;
  children: ReactNode;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="rounded-full border border-line bg-white/80 px-3 py-1 text-xs text-muted transition hover:border-accent/40 hover:text-ink"
    >
      {children}
    </button>
  );
}
