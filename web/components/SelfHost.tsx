const GITHUB = "https://github.com/aryanjohari/pii-gateway";

const SNIPPET = `git clone https://github.com/aryanjohari/pii-gateway.git
cd pii-gateway
cp .env.example .env
# set SANITIZE_HTTP_API_KEY in .env
docker compose up --build`;

export function SelfHost() {
  return (
    <section
      id="self-host"
      className="animate-rise scroll-mt-8 max-w-3xl"
      style={{ animationDelay: "160ms" }}
    >
      <h2 className="font-display text-3xl font-bold tracking-tight text-ink sm:text-4xl">
        Self-host
      </h2>
      <p className="mt-3 max-w-xl text-muted">
        Run the same container locally or on a home lab (including Raspberry Pi
        arm64). Compose is the primary path.
      </p>
      <pre className="mt-6 overflow-x-auto rounded-2xl border border-line bg-ink p-5 font-mono text-sm leading-relaxed text-paper shadow-soft">
        {SNIPPET}
      </pre>
      <div className="mt-6 flex flex-wrap gap-4 text-sm">
        <a
          href={GITHUB}
          target="_blank"
          rel="noreferrer"
          className="font-medium text-accent underline-offset-4 hover:underline"
        >
          GitHub repository
        </a>
        <a
          href={`${GITHUB}/blob/main/docs/DEPLOY_PI.md`}
          target="_blank"
          rel="noreferrer"
          className="font-medium text-muted underline-offset-4 hover:underline hover:text-ink"
        >
          Pi deploy checklist
        </a>
        <a
          href={`${GITHUB}/blob/main/docs/c4/README.md`}
          target="_blank"
          rel="noreferrer"
          className="font-medium text-muted underline-offset-4 hover:underline hover:text-ink"
        >
          Architecture (C4)
        </a>
      </div>
    </section>
  );
}
