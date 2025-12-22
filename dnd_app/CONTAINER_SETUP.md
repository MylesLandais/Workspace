# Running in Containers

## Option 1: Docker Compose (Recommended)

This is the easiest way to run everything in containers.

**For comprehensive Docker deployment documentation, see [DOCKER_DEPLOYMENT.md](DOCKER_DEPLOYMENT.md).**

### Prerequisites
- Docker and Docker Compose installed

### Quick Start

```bash
cd dnd_app
docker-compose up
```

This will:
1. Start Neo4j in a container (with health checks)
2. Build and start the Phoenix app in a container (using Bun for assets)
3. Connect them automatically via Docker networking

### Access the App

- **Phoenix app**: http://localhost:4000
- **Neo4j Browser**: http://localhost:7474 (username: `neo4j`, password: `password`)

### Stop Everything

```bash
docker-compose down
```

### View Logs

```bash
docker-compose logs -f dnd-app
docker-compose logs -f neo4j
```

### Building Assets

Assets are built using Bun. To rebuild assets in the container:

```bash
docker-compose exec dnd-app sh -c "cd assets && bun run build"
```

For development with hot-reload:

```bash
docker-compose exec dnd-app sh -c "cd assets && bun run watch"
```

## Option 2: Use Existing Neo4j Container

If you already have Neo4j running (I see you have a `neo4j` container), you can:

### Check Neo4j Container

```bash
docker ps | grep neo4j
```

### Update Connection

If your Neo4j container uses different credentials or network, update `config/config.exs`:

```elixir
config :bolt_sips, Bolt,
  url: "bolt://localhost:7687",  # or use container IP
  basic_auth: [username: "neo4j", password: "your_password"],
```

### Run Phoenix App Locally

```bash
cd dnd_app
mix deps.get
cd assets && npm install && cd ..
mix phx.server
```

## Option 3: Run Phoenix in Existing Container

If you want to run the Phoenix app inside your `jupyter` container:

### Check if Elixir is Available

```bash
docker exec jupyter which elixir
docker exec jupyter which mix
```

### If Elixir is Available

```bash
# Copy project into container (or mount volume)
docker cp dnd_app jupyter:/workspace/dnd_app

# Enter container
docker exec -it jupyter bash

# Inside container:
cd /workspace/dnd_app
mix deps.get
cd assets && npm install && cd ..
mix phx.server
```

### If Elixir is NOT Available

You'll need to either:
1. Install Elixir in the container, OR
2. Use Docker Compose (Option 1), OR
3. Run locally and connect to existing Neo4j (Option 2)

## Network Configuration

### Docker Compose Network

When using `docker-compose.yml`, services can communicate using service names:
- Phoenix app connects to Neo4j using: `bolt://neo4j:7687`

### External Neo4j

If using an external Neo4j container, you may need to:
- Use `host.docker.internal` (Mac/Windows) or container IP
- Or connect both to the same Docker network

## Troubleshooting

### Can't Connect to Neo4j from Container

1. Check Neo4j is running: `docker ps | grep neo4j`
2. Check network: Containers must be on same network
3. Use service name in docker-compose, or container IP for external

### Port Already in Use

If port 4000 is taken, change in `docker-compose.yml`:
```yaml
ports:
  - "4001:4000"  # Map host 4001 to container 4000
```

### Assets Not Loading

Make sure assets are compiled:
```bash
docker-compose exec dnd-app mix assets.deploy
```

## Quick Reference

```bash
# Start everything
docker-compose up

# Start in background
docker-compose up -d

# View logs
docker-compose logs -f

# Stop everything
docker-compose down

# Rebuild after code changes
docker-compose up --build

# Run commands in container
docker-compose exec dnd-app mix test
```





