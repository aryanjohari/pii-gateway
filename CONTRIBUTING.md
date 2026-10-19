# Contributing

Thank you for your interest in PII Gateway.

## Development

- Python 3.11+
- Install with dev extras: `pip install -e ".[dev]"`
- Run tests: `pytest`
- Lint: `ruff check src tests`
- Typecheck: `mypy src`

### Pre-commit (optional, recommended)

Runs `ruff check` and `ruff format` on `src` and `tests` before each commit, so style failures
are caught locally instead of in CI. CI itself does not depend on it.

- Install the tool once: `pip install pre-commit`
- Enable it in your clone: `pre-commit install`
- Run it on everything: `pre-commit run --all-files`
- Update the pinned ruff version: edit `rev` in `.pre-commit-config.yaml`, matching the ruff version you lint with.

## Pull requests

- Keep changes focused; match existing style (`snake_case`, strict typing, Pydantic v2).
- Do not log raw request bodies, SQL row payloads, or file contents.
- Add or update tests for redaction and security-sensitive paths.

## Security

Please report security issues privately to the maintainers (do not open a public issue for undisclosed vulnerabilities).
