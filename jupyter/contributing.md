# Contributing

## Environment setup

This is a NixOS system. Use `uv` for Python dependency management.

```bash
# install dependencies
uv venv
uv pip install -e ".[dev]"

# start PostgreSQL
docker compose up -d

# verify
pytest tests/ -v
python -c "from lib.db.client import get_db"
python -c "from lib.otel import get_tracer"
```

## Directory conventions

```
infra/    Infrastructure (database connections, extensions, schemas, migrations)
lib/      Shared libraries consumed by all applications and notebooks
src/      Client applications only -- each app imports from lib/ and infra/
tests/    Mirrors infra/ and lib/ structure
notebooks/  Exploratory and analysis work
data/     Inputs, outputs, datasets, archives
```

lib/ is for reusable code. src/ is for applications that wire lib/ modules together
with HTTP routes, CLI entry points, or worker loops. Do not put shared logic in src/.

## Development workflow

Write tests first, then implementation. Minimum 33% coverage on new code.

```bash
# run tests
pytest tests/ -v --tb=short

# run with coverage
pytest tests/ --cov=lib --cov=infra --cov-report=term-missing

# start the feed API
uvicorn src.feed.web.server:app --port 8080
```

## Dependency management

Use `uv` for Python packages. Add runtime dependencies to `pyproject.toml`
under `[project.dependencies]`. Add test-only dependencies under
`[project.optional-dependencies] dev`.

Prefer small, well-maintained packages. Pin versions where reproducibility
matters. Document why non-trivial dependencies were added.

## Commit conventions

Follow Conventional Commits: https://www.conventionalcommits.org/

```
<type>[scope]: description
```

Types: feat, fix, docs, style, refactor, perf, test, build, chore, ci.
Imperative mood, under 72 characters, no trailing period. Body explains why.

## Security

- Never commit secrets. Use `.env` for API keys and tokens.
- Talisman pre-commit hook scans for leaked credentials.
- Review `.gitignore` before staging files.

## Code style

- No emojis in code or documentation.
- Python: snake_case, type hints where appropriate.
- File naming: lowercase with hyphens for docs (readme.md, not README.md).
- Prefer editing existing files over creating new ones.
