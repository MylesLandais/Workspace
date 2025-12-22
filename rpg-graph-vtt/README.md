# RPG Graph VTT - Graph-Powered D&D 5e Character Management

A Neo4j-backed character management system for Dungeons & Dragons 5th Edition that enables character creation, party viewing, AI agent integration, and 3D dice rolling through a semantic graph database architecture.

## Quick Start

### In Docker Container

```bash
# Start the web server
docker exec -it jupyter bash
cd /home/jovyan/workspaces/rpg-graph-vtt/web
python server.py
```

Access at: http://localhost:8000

### Local Development

```bash
cd rpg-graph-vtt/web
python server.py
```

## Features

- **Graph-Native Storage**: All character data stored as nodes and relationships in Neo4j
- **D&D 5e Compatibility**: Full support for D&D 5e character creation and progression
- **3D Dice Rolling**: Deterministic physics-based dice animations (D&D Beyond style)
- **Foundry VTT Interoperability**: Import/export characters in Foundry VTT JSON format
- **AI Agent Integration**: Game Master (GM) Agent and Character Assistant Agent powered by Google ADK
- **Party Management**: View and manage multiple characters as a cohesive party
- **Web Frontend**: FastAPI server with HTML/CSS/JS character sheet viewer

## Project Structure

```
rpg-graph-vtt/
├── rpg_graph_vtt/          # Python package
│   ├── models/             # Pydantic data models
│   ├── graph/              # Neo4j operations
│   ├── converters/         # Import/export converters
│   ├── tools.py            # AI agent tools
│   ├── agent.py            # Agent definitions
│   └── prompt.py           # Agent prompts
├── client/                 # Frontend code
│   ├── src/               # Source files (reserved for build pipeline)
│   ├── static/            # Static assets (HTML, CSS, JavaScript)
│   └── README.md
├── web/                    # Backend API server
│   ├── api/               # API modules
│   │   ├── routes/        # API route handlers
│   │   ├── models/        # API response models
│   │   └── dependencies.py
│   ├── server.py           # FastAPI app initialization
│   └── README.md
├── database/               # Database schema and migrations
│   ├── migrations/        # Neo4j schema migrations (Cypher)
│   ├── seeds/             # Data seeds (D&D 5e content)
│   ├── schema/            # Programmatic schema definitions
│   ├── docs/              # Database documentation
│   └── README.md
├── tests/                  # Test suite
│   ├── unit/              # Unit tests
│   ├── integration/       # Integration tests
│   ├── fixtures/          # Test fixtures
│   └── README.md
├── notebooks/              # Jupyter notebooks
│   ├── 01_neo4j_setup.ipynb
│   ├── 02_character_creation.ipynb
│   └── 03_party_viewing.ipynb
└── README.md
```

## Documentation

- **[Integration Guide](INTEGRATION.md)** - Monorepo integration details
- **[Client Quick Start](client/QUICKSTART.md)** - Frontend development
- **[Web Server](web/README.md)** - API server setup
- **[Database](database/README.md)** - Schema and migrations
- **[Testing Guide](tests/README.md)** - Test suite documentation
- **[Specification](spec.md)** - Complete system specification

## Dependencies

All dependencies are managed at the monorepo root level:
- See `../requirements.txt` and `../pyproject.toml`

Key dependencies:
- Neo4j 5.x+ (Bolt protocol)
- FastAPI 0.100+
- Google ADK 1.0+ (for AI agents)
- Three.js (CDN, for dice rolling)

## Environment Setup

Create `.env` file in monorepo root with:

```bash
NEO4J_URI=neo4j+s://your-instance.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your-password
```

The connection manager automatically detects Docker vs local environment.

## License

Apache 2.0
