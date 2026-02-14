# jupyter workspace

Monorepo for feed monitoring, VTT, image generation, and media tools.

## Structure

```
infra/           PostgreSQL (pgVector + AGE), ComfyUI docker/workflows
lib/             Shared libraries (db, otel, sources, comfy, dedup, vtt, arena, media, utils)
src/             Applications (feed, vtt, crawlers, discord)
tests/           Test suite (mirrors infra/ and lib/)
notebooks/       Jupyter notebooks (experiments, analysis, comfy)
data/            Inputs (prompts, character cards), outputs, datasets, archives
config/          Configuration files
docker/          Docker compose and related files
```

### lib/ modules

- `lib/db` -- database client wrapping infra/psql
- `lib/otel` -- OpenTelemetry tracing, metrics, span helpers
- `lib/sources` -- platform connectors (reddit, youtube, tumblr, imageboard)
- `lib/comfy` -- ComfyUI client, templates, metadata, agent tooling
- `lib/dedup` -- image deduplication (hashing, detection, clustering)
- `lib/vtt` -- RPG game mechanics (models, graph, converters)
- `lib/arena` -- ASR + TTS model evaluation
- `lib/media` -- captioning, image crawling
- `lib/utils` -- file renaming, DVD processing, subtitle tools

### src/ applications

- `src/feed` -- social media feed app (FastAPI REST, crawlers, archivers)
- `src/vtt` -- VTT web app (FastAPI, wraps lib/vtt)
- `src/crawlers` -- crawler orchestration and workers
- `src/discord` -- discord bot (midjourney clone, uses lib/comfy)

## Quick start

Requires NixOS with uv and CUDA toolkit.

```bash
git clone git@github.com:MylesLandais/jupyter.git
cd jupyter
cp .env.example .env       # edit with your API keys

# create venv and install
uv venv
uv pip install -e ".[dev]"

# start services
docker compose up -d       # PostgreSQL, etc.

# run tests
pytest tests/ -v
```

## Environment

Create `.env` from `.env.example`. Required variables:

```
POSTGRES_HOST, POSTGRES_PORT, POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB
OTEL_EXPORTER_OTLP_ENDPOINT, OTEL_SERVICE_NAME
RUNPOD_API_KEY, RUNPOD_S3_ACCESS_KEY, RUNPOD_S3_SECRET_KEY
OPENROUTER_API_KEY
HUGGINGFACE_TOKEN
```

## Services

- FastAPI REST API: `uvicorn src.feed.web.server:app --port 8080`
- API docs: http://localhost:8080/docs
- PostgreSQL: localhost:5432 (pgVector + Apache AGE)
- ComfyUI: localhost:8188 (local) or RunPod serverless
