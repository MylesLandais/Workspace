# Web Server - FastAPI Backend

FastAPI server that serves the frontend and provides the REST API.

## Structure

```
web/
├── api/                    # API modules
│   ├── routes/             # Route handlers
│   │   ├── characters.py   # Character endpoints
│   │   ├── parties.py      # Party endpoints
│   │   └── game_system.py  # Classes, races, etc.
│   ├── models/             # API response models
│   │   └── responses.py    # CharacterResponse, PartyResponse
│   └── dependencies.py     # Shared dependencies (DB connection)
├── server.py               # FastAPI app initialization
└── README.md
```

## Quick Start

### From Project Root

```bash
cd rpg-graph-vtt/web
python server.py
```

Or use the start script:

```bash
./rpg-graph-vtt/web/start.sh
```

### From Docker Container

```bash
docker exec -it jupyter bash
cd /home/jovyan/workspaces/rpg-graph-vtt/web
python server.py
```

## Access

Once running, access the application at:
- **Main Character Sheet**: http://localhost:8000
- **Dice Roller Demo**: http://localhost:8000/static/dice-roller.html
- **API Docs**: http://localhost:8000/docs (FastAPI Swagger UI)

## API Endpoints

### Characters
- `GET /api/characters` - List all characters
- `GET /api/characters/{uuid}` - Get specific character

### Parties
- `GET /api/parties` - List all parties with characters
- `GET /api/parties/{name}` - Get specific party

### Game System
- `GET /api/classes` - List all classes
- `GET /api/races` - List all races

## API Architecture

The API is organized into modular route handlers:
- **routes/**: Separate files for each resource (characters, parties, game_system)
- **models/**: Pydantic response models for API responses
- **dependencies.py**: Shared dependencies like database connection

This modular structure makes the API easier to test and maintain.

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

## API Design

The API follows REST principles:
- **REST for MVP**: Simple REST endpoints, no GraphQL complexity
- **Modular Routes**: Each resource has its own route file
- **Dependency Injection**: Database connection injected via FastAPI dependencies
- **Response Models**: Typed Pydantic models for all responses

Future enhancements may include GraphQL support when needed.
