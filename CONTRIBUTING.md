# Contributing

Thank you for your interest in PII Gateway.

## Development

- Python 3.11+
- Install with dev extras: `pip install -e ".[dev]"`
- Run tests: `pytest`
- Lint: `ruff check src tests`
- Typecheck: `mypy src`

## Pull requests

- Keep changes focused; match existing style (`snake_case`, strict typing, Pydantic v2).
- Do not log raw request bodies, SQL row payloads, or file contents.
- Add or update tests for redaction and security-sensitive paths.

## Security

Please report security issues privately to the maintainers (do not open a public issue for undisclosed vulnerabilities).
