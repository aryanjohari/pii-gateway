const GITHUB = "https://github.com/aryanjohari/pii-gateway";

export function Footer() {
  return (
    <footer className="mt-24 border-t border-line pt-8 text-sm text-muted">
      <p>
        PII Gateway is a personal / learning project. It is not a compliance product
        and the public demo must not receive real personal data.
      </p>
      <div className="mt-4 flex flex-wrap gap-4">
        <a href={GITHUB} className="hover:text-ink" target="_blank" rel="noreferrer">
          GitHub
        </a>
        <a
          href={`${GITHUB}/blob/main/LICENSE`}
          className="hover:text-ink"
          target="_blank"
          rel="noreferrer"
        >
          MIT License
        </a>
        <a href="#top" className="hover:text-ink">
          Back to top
        </a>
      </div>
    </footer>
  );
}
