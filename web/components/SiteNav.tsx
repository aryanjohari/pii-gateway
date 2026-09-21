const GITHUB = "https://github.com/aryanjohari/pii-gateway";

export function SiteNav() {
  return (
    <header className="flex items-center justify-between gap-4">
      <a href="#top" className="font-display text-sm font-semibold tracking-wide text-ink">
        PII Gateway
      </a>
      <nav className="flex items-center gap-5 text-sm text-muted">
        <a href="#demo" className="transition hover:text-ink">
          Demo
        </a>
        <a href="#self-host" className="transition hover:text-ink">
          Self-host
        </a>
        <a
          href={GITHUB}
          target="_blank"
          rel="noreferrer"
          className="transition hover:text-ink"
        >
          GitHub
        </a>
      </nav>
    </header>
  );
}
