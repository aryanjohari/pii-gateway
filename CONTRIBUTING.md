# Contributing

Thank you for your interest in PII Gateway.

## Development

- Python 3.11+
- Install with dev extras, using the pinned versions: `pip install -c constraints.txt -e ".[dev]"`
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

### Updating pinned dependencies

`constraints.txt` fixes the version of every package CI and the Docker image install, so a new
upstream release cannot break a build unnoticed. It is a pip constraints file: it limits versions
but does not add packages, so new dependencies still go in `pyproject.toml`.

To refresh it, from a clean Python 3.12 virtual environment:

```
pip install -e ".[dev]"
pip freeze --exclude-editable | sort -f > constraints.txt
```

Then re-add the three header comment lines, run the full test suite, and commit the file on its own.
The spaCy model (`en_core_web_sm`) is downloaded separately and is not pinned here.

## Pull requests

- Keep changes focused; match existing style (`snake_case`, strict typing, Pydantic v2).
- Do not log raw request bodies, SQL row payloads, or file contents.
- Add or update tests for redaction and security-sensitive paths.

## Security

Please report security issues privately to the maintainers (do not open a public issue for undisclosed vulnerabilities).
