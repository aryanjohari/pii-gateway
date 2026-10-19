import { markRedactions } from "@/lib/markRedactions";

type Props = {
  mode: "text" | "json";
  original: string;
  redacted: string;
};

export function BeforeAfter({ mode, original, redacted }: Props) {
  // Markers only make sense for free text; JSON output is re-serialised, so offsets do not line up.
  const segments = mode === "text" ? markRedactions(original, redacted) : null;

  return (
    <div className="grid gap-0 border-t border-line md:grid-cols-2">
      <section
        aria-labelledby="before-heading"
        className="border-b border-line p-4 md:border-b-0 md:border-r"
      >
        <h3
          id="before-heading"
          className="mb-2 text-xs font-medium uppercase tracking-wider text-muted"
        >
          Your text
        </h3>
        <div className="whitespace-pre-wrap break-words rounded-xl bg-mist/40 p-3 font-mono text-sm leading-relaxed text-ink">
          {segments
            ? segments.map((segment, index) =>
                segment.kind === "text" ? (
                  <span key={index}>{segment.text}</span>
                ) : (
                  <span key={index}>
                    <mark className="rounded bg-accent-soft px-0.5 text-ink underline decoration-accent decoration-2 underline-offset-2">
                      {segment.text}
                    </mark>
                    <span className="ml-1 rounded border border-accent px-1 text-xs text-accent">
                      {segment.label}
                    </span>
                  </span>
                ),
              )
            : original}
        </div>
      </section>

      <section aria-labelledby="after-heading" className="p-4">
        <h3
          id="after-heading"
          className="mb-2 text-xs font-medium uppercase tracking-wider text-muted"
        >
          What the AI would see
        </h3>
        <pre className="whitespace-pre-wrap break-words rounded-xl bg-mist/40 p-3 font-mono text-sm leading-relaxed text-ink">
          {redacted}
        </pre>
        <p className="mt-2 text-xs text-muted">
          This is the prompt that would be sent. The demo does not call an AI model.
        </p>
      </section>
    </div>
  );
}
