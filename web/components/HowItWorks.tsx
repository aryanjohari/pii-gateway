const STEPS = [
  {
    title: "Send HTTP JSON",
    body: "Call POST /v1/sanitize with free text and/or nested structured fields.",
  },
  {
    title: "Apply policy + Presidio",
    body: "Declared fields use deterministic rules; undeclared strings get best-effort NLP. Placeholders look like <EMAIL_ADDRESS>.",
  },
  {
    title: "Return cleaned data",
    body: "Get redacted output and entity counts for logs, analytics, or experiments—no accuracy guarantees.",
  },
];

export function HowItWorks() {
  return (
    <section className="animate-rise max-w-3xl" style={{ animationDelay: "120ms" }}>
      <h2 className="font-display text-3xl font-bold tracking-tight text-ink sm:text-4xl">
        How it works
      </h2>
      <ol className="mt-8 space-y-8">
        {STEPS.map((step, index) => (
          <li key={step.title} className="grid grid-cols-[auto_1fr] gap-4">
            <span className="font-display text-2xl font-bold text-accent/80">
              {String(index + 1).padStart(2, "0")}
            </span>
            <div>
              <h3 className="text-xl font-semibold text-ink">{step.title}</h3>
              <p className="mt-1 leading-relaxed text-muted">{step.body}</p>
            </div>
          </li>
        ))}
      </ol>
    </section>
  );
}
