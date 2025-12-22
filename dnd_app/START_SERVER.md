# How to Start the Server for Preview

## Quick Start

```bash
cd dnd_app

# 1. Install dependencies
mix deps.get
cd assets && npm install && cd ..

# 2. Make sure Neo4j is running
# (See Neo4j setup below)

# 3. Start the Phoenix server
mix phx.server
```

Then open your browser to: **http://localhost:4000**

## Neo4j Setup

### Option 1: Docker (Recommended)

```bash
docker run -d \
  --name neo4j-dnd \
  -p 7474:7474 \
  -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/password \
  neo4j:5-community
```

### Option 2: Local Installation

If you have Neo4j installed locally, make sure it's running on port 7687.

### Verify Neo4j Connection

The app will attempt to connect to Neo4j on startup. Check the logs for:
- ✅ "Neo4j schema initialized successfully"
- ❌ "Failed to initialize Neo4j schema" (check connection settings)

## Troubleshooting

### Port Already in Use

If port 4000 is already in use, you can change it in `config/dev.exs`:

```elixir
http: [ip: {127, 0, 0, 1}, port: 4001],  # Change to different port
```

### Assets Not Loading

If CSS/JS don't load, compile assets:

```bash
mix assets.deploy
# or in dev mode, they should compile automatically
```

### Neo4j Connection Issues

1. Check Neo4j is running: `docker ps | grep neo4j`
2. Verify credentials in `config/config.exs`
3. Test connection: `cypher-shell -u neo4j -p password`

### Dependencies Issues

```bash
# Clean and reinstall
rm -rf deps _build
mix deps.get
mix deps.compile
```

## Development Features

- **Hot Reload**: Code changes automatically reload
- **Live Reload**: Browser automatically refreshes on file changes
- **Debug Mode**: Detailed error pages in development

## Production Build

For production preview:

```bash
MIX_ENV=prod mix deps.get --only prod
MIX_ENV=prod mix compile
MIX_ENV=prod mix assets.deploy
MIX_ENV=prod mix phx.server
```





