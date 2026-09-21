export function Hero() {
  return (
    <section id="top" className="animate-rise max-w-3xl">
      <p className="font-display text-5xl font-extrabold leading-[0.95] tracking-tight text-ink sm:text-7xl">
        PII Gateway
      </p>
      <h1 className="mt-6 max-w-2xl text-2xl font-medium leading-snug text-ink sm:text-3xl">
        Scrub personal data from text and JSON before it leaves your boundary.
      </h1>
      <p className="mt-5 max-w-xl text-lg leading-relaxed text-muted">
        A Docker-first FastAPI service powered by Microsoft Presidio and a mounted
        policy file—centralize redaction for analytics, logs, and experiments.
      </p>
      <div className="mt-9 flex flex-wrap items-center gap-3">
        <a
          href="#demo"
          className="rounded-full bg-accent px-6 py-3 text-sm font-medium text-white transition hover:brightness-110"
        >
          Try the demo
        </a>
        <a
          href="#self-host"
          className="rounded-full border border-line bg-white/60 px-6 py-3 text-sm font-medium text-ink transition hover:border-ink/30"
        >
          Self-host
        </a>
      </div>
    </section>
  );
}
