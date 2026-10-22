const GITHUB = "https://github.com/aryanjohari/pii-gateway";

export function LimitsNote() {
  return (
    <aside aria-labelledby="limits-heading" className="mt-6 max-w-3xl text-sm leading-relaxed">
      <h3 id="limits-heading" className="font-semibold text-ink">
        What this can miss
      </h3>
      <p className="mt-2 text-muted">
        This is best-effort redaction, not a guarantee, and not a compliance product. A
        missed item reaches the AI, so check the right-hand panel before you rely on it.
      </p>
      <ul className="mt-2 list-disc space-y-1 pl-5 text-muted">
        <li>Names in free text can be missed.</li>
        <li>An NHI or IRD number with a mistyped check digit is not redacted.</li>
        <li>Driver licence numbers match by shape only, so look-alike codes are redacted too.</li>
        <li>The highlights in the left panel are recovered from the output and may be off.</li>
      </ul>
      <p className="mt-2 text-muted">
        Accuracy numbers are in the{" "}
        <a
          href={`${GITHUB}#evaluation`}
          target="_blank"
          rel="noreferrer"
          className="font-medium text-accent underline underline-offset-4"
        >
          evaluation
        </a>{" "}
        and{" "}
        <a
          href={`${GITHUB}#nz-identifiers`}
          target="_blank"
          rel="noreferrer"
          className="font-medium text-accent underline underline-offset-4"
        >
          NZ identifiers
        </a>{" "}
        sections (precision and recall). They come from synthetic sentences written by the
        same person who wrote the detectors, so real text will score lower. The demo&apos;s
        combined policy has no measurement of its own yet.
      </p>
    </aside>
  );
}
