# Archive Web Viewer

A lightweight, Python-powered web interface for exploring imageboard archival datasets.

## Features

- **Advanced Search:** Filter by text, board, date range, and image presence.
- **Gallery View:** High-density grid for visual exploration.
- **Thread Context:** View full thread conversations in a classic board layout.
- **Parquet-Native:** Reads directly from archival datasets for maximum performance.

## Development

The service is built with Flask and Pandas.

### Running with Docker

```bash
docker compose up -d archive_web
```

### Running Tests

Tests are written with `pytest` and can be run inside the container:

```bash
docker exec archive_web pytest test_app.py
```

## Architecture

- `app.py`: Main Flask application (Single-file for simplicity).
- `test_app.py`: Integration tests for routes and data logic.
- `Dockerfile`: Minimal Python 3.11 environment.
- `requirements.txt`: Minimal dependencies (Flask, Pandas, PyArrow).
