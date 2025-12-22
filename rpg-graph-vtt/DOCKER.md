# Docker Usage Guide

## Quick Commands

### Start Web Server

```bash
docker exec -it jupyter bash
cd /home/jovyan/workspaces/rpg-graph-vtt/web
python server.py
```

Or run in background:
```bash
docker exec -d jupyter bash -c "cd /home/jovyan/workspaces/rpg-graph-vtt/web && python server.py"
```

### Run Notebooks

```bash
docker exec -it jupyter bash
cd /home/jovyan/workspaces/rpg-graph-vtt/notebooks
jupyter notebook
```

### Install Dependencies

If you add new dependencies to `requirements.txt`:

```bash
# Rebuild container (recommended)
docker compose build jupyterlab

# Or install in running container
docker exec -it jupyter pip install <package>
```

### Check Logs

```bash
docker logs jupyter
```

## Path Reference

- **Monorepo Root**: `/home/jovyan/workspaces/`
- **Project Root**: `/home/jovyan/workspaces/rpg-graph-vtt/`
- **Environment File**: `/home/jovyan/workspaces/.env`
- **Web Server**: `/home/jovyan/workspaces/rpg-graph-vtt/web/`
- **Client Files**: `/home/jovyan/workspaces/rpg-graph-vtt/client/static/`

## Ports

- **Jupyter Lab**: 8888
- **RPG Graph VTT API**: 8000

Both are exposed in `docker-compose.yml`.

## Environment Variables

The connection manager automatically looks for `.env` at:
1. `/home/jovyan/workspaces/.env` (Docker - checked first)
2. Current directory `.env` (fallback)
3. `~/Workspace/jupyter/.env` (local dev fallback)

## Troubleshooting

### Port Already in Use

```bash
# Find what's using port 8000
docker exec jupyter lsof -i :8000

# Or use different port
docker exec -it jupyter bash
cd /home/jovyan/workspaces/rpg-graph-vtt/web
uvicorn server:app --host 0.0.0.0 --port 8001
```

### Module Not Found

If imports fail, ensure the package is installed:
```bash
docker exec -it jupyter pip install -e /home/jovyan/workspaces
```

### Neo4j Connection Issues

Check environment variables:
```bash
docker exec jupyter env | grep NEO4J
```

Verify `.env` file exists:
```bash
docker exec jupyter ls -la /home/jovyan/workspaces/.env
```



