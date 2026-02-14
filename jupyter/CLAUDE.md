# Project: jupyter workspace

Monorepo for feed monitoring, VTT, image generation, and media tools.
NixOS system. Use `uv` for Python, `docker compose` (space not hyphen).

## Structure

```
infra/psql/      PostgreSQL connection, AGE adapter, extensions, schemas, migrations
infra/comfyui/   Dockerfile, extra_model_paths.yaml, workflows/
lib/db/          Shared database client (get_db, get_graph, SQLAlchemy models)
lib/otel/        OpenTelemetry tracing, metrics, @traced decorator
lib/sources/     Platform connectors (reddit, youtube, tumblr, imageboard)
lib/comfy/       ComfyUI client, metadata, agent, projects
lib/dedup/       Image deduplication
lib/vtt/         RPG game mechanics (models, graph, converters)
lib/arena/       ASR + TTS evaluation
lib/media/       Captioning, image crawling
lib/utils/       File renaming, DVD processing, subtitles
src/feed/        Feed monitoring app (FastAPI REST API)
src/vtt/         VTT web app (FastAPI, wraps lib/vtt)
src/crawlers/    Crawler orchestration and workers
src/discord/     Discord bot
tests/           Mirrors infra/ and lib/
notebooks/       Jupyter notebooks
data/            Inputs (prompts, character cards), outputs, datasets, archives
```

## Key patterns

- lib/ = shared code, src/ = applications. Never put shared logic in src/.
- All database access goes through lib/db/client.py (wraps infra/psql/).
- OTel available everywhere via lib/otel/ (get_tracer, get_meter, @traced).
- Platform connectors inherit from lib/sources/base.py (PlatformAdapter ABC).
- PostgreSQL with pgVector + Apache AGE. No Neo4j.
- Config via environment variables only. No hardcoded paths.

## Development

- TDD: write tests first, then implementation. Minimum 33% coverage.
- Tests: `pytest tests/ -v --tb=short`
- Coverage: `pytest tests/ --cov=lib --cov=infra --cov-report=term-missing`
- Feed API: `uvicorn src.feed.web.server:app --port 8080`
- API docs: http://localhost:8080/docs

## Dependencies

Managed via pyproject.toml. Use `uv add` / `uv remove`.
Runtime deps in [project.dependencies], test deps in [project.optional-dependencies] dev.

## Conventions

- Conventional Commits (feat, fix, refactor, test, etc.)
- No emojis. No ALL CAPS filenames (use lowercase-with-hyphens.md).
- Prefer editing existing files over creating new ones.
- Python: snake_case, type hints where appropriate.
