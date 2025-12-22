# Monorepo Integration Guide

This document explains how rpg-graph-vtt is integrated into the larger jupyter monorepo.

## Structure

```
jupyter/
├── rpg-graph-vtt/          # RPG Graph VTT project
│   ├── rpg_graph_vtt/      # Python package (installable)
│   ├── client/             # Frontend code
│   │   ├── src/            # Source files (reserved for build pipeline)
│   │   └── static/         # Static assets (HTML, CSS, JS)
│   ├── web/                # FastAPI server
│   │   ├── api/            # API modules (routes, models, dependencies)
│   │   └── server.py       # FastAPI app
│   ├── database/           # Neo4j migrations & docs
│   │   ├── migrations/     # Schema migrations
│   │   ├── seeds/          # Data seeds
│   │   └── schema/         # Programmatic schema definitions
│   ├── tests/              # Test suite
│   └── notebooks/          # Jupyter notebooks
├── src/                    # Shared monorepo code
├── requirements.txt        # Root-level dependencies (includes rpg-graph-vtt deps)
└── pyproject.toml          # Root-level project config
```

## Docker Integration

The project is designed to work within the Docker container environment:

- **Workspace Mount**: `/home/jovyan/workspaces` (note: plural)
- **Environment File**: `/home/jovyan/workspaces/.env`
- **Package Installation**: Installed in editable mode via root `pyproject.toml`

## Dependencies

RPG Graph VTT dependencies are included in:
- `requirements.txt` - For pip installation
- `pyproject.toml` - For setuptools installation

Key dependencies:
- `neo4j>=5.0.0` - Graph database driver
- `fastapi>=0.100.0` - Web framework
- `uvicorn[standard]>=0.23.0` - ASGI server
- `pydantic-settings>=2.8.1` - Settings management

## Running in Docker

### Start the Web Server

```bash
docker exec -it jupyter bash
cd /home/jovyan/workspaces/rpg-graph-vtt/web
python server.py
```

Or from host:
```bash
docker exec -d jupyter bash -c "cd /home/jovyan/workspaces/rpg-graph-vtt/web && python server.py"
```

### Access the Application

- **Character Sheet**: http://localhost:8000
- **Dice Roller Demo**: http://localhost:8000/static/dice-roller.html
- **API Docs**: http://localhost:8000/docs

### Run Notebooks

```bash
docker exec -it jupyter bash
cd /home/jovyan/workspaces/rpg-graph-vtt/notebooks
jupyter notebook 01_neo4j_setup.ipynb
```

## Environment Configuration

The connection manager automatically detects the environment:

1. **Docker**: Looks for `/home/jovyan/workspaces/.env`
2. **Local**: Looks for `.env` in current directory or `~/Workspace/jupyter/.env`

Set these variables in your `.env` file:
```bash
NEO4J_URI=neo4j+s://your-instance.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your-password
```

## Package Imports

The `rpg_graph_vtt` package can be imported from anywhere in the monorepo:

```python
from rpg_graph_vtt.graph.connection import get_connection
from rpg_graph_vtt.graph.queries import CharacterQueries
from rpg_graph_vtt.models.character import Character
from rpg_graph_vtt.agent import create_gm_agent
```

## Development Workflow

1. **Edit code** in `rpg-graph-vtt/`
2. **Restart server** (if needed):
   ```bash
   docker exec -it jupyter bash
   cd /home/jovyan/workspaces/rpg-graph-vtt/web
   python server.py
   ```
3. **Test changes** at http://localhost:8000

## Adding New Dependencies

1. Add to `rpg-graph-vtt/pyproject.toml` (for project-specific deps)
2. Add to root `requirements.txt` (if shared across monorepo)
3. Rebuild Docker container or install in running container:
   ```bash
   docker exec -it jupyter pip install <package>
   ```

## File Paths

All paths are relative to the monorepo root:
- **Docker**: `/home/jovyan/workspaces/rpg-graph-vtt/...`
- **Local**: `~/Workspace/jupyter/rpg-graph-vtt/...`

The connection manager handles path resolution automatically.

