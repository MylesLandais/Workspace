# Web Server - FastAPI Backend

FastAPI server that serves the frontend and provides the REST API.

## Quick Start

### From Project Root

```bash
cd agents/rpg-graph-vtt/web
python server.py
```

Or use the start script:

```bash
./agents/rpg-graph-vtt/web/start.sh
```

### From Docker Container

```bash
docker exec -it jupyter bash
cd /home/jovyan/workspace/agents/rpg-graph-vtt/web
python server.py
```

## Access

Once running, access the application at:
- **Main Character Sheet**: http://localhost:8000
- **Dice Roller Demo**: http://localhost:8000/static/dice-roller.html
- **API Docs**: http://localhost:8000/docs (FastAPI Swagger UI)

## Port Configuration

The server runs on port 8000 by default. This is already exposed in `docker-compose.yml`:
- Host port: `8000`
- Container port: `8000`

## Static Files

The server automatically serves files from `../client/static/` at the `/static/` URL path:
- CSS: `/static/css/dice-roller.css`
- JavaScript: `/static/js/dice-visualizer.js`
- HTML: `/static/dice-roller.html`

## Development

The server uses `reload=True` when run directly, so it will auto-reload on code changes.

For production, use:
```bash
uvicorn server:app --host 0.0.0.0 --port 8000
```
