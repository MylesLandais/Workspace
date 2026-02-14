# Docker Deployment Guide

Complete guide for deploying the Phoenix-Ash D&D application with Docker, TypeScript, and Bun for local development.

## Quick Start

```bash
# Start everything with Docker Compose
docker-compose up

# Access the application
# - Phoenix app: http://localhost:4000
# - Neo4j Browser: http://localhost:7474 (username: neo4j, password: password)
```

## Overview

This guide covers:
- Docker Compose setup with Neo4j and Phoenix
- TypeScript migration (strict mode)
- Bun runtime for asset management
- Network configuration and troubleshooting
- Development workflow

## Architecture

### Service Architecture

```
┌─────────────────┐         ┌──────────────────┐
│   Phoenix App   │────────▶│      Neo4j       │
│  (dnd-app)      │  Bolt   │   (neo4j:7687)   │
│  Port: 4000     │ Protocol│  Ports: 7474/7687│
└─────────────────┘         └──────────────────┘
       │
       │ HTTP/WebSocket
       ▼
┌─────────────────┐
│   Web Browser   │
│  localhost:4000 │
└─────────────────┘
```

### Data Flow

1. **Client** → Sends requests to Phoenix (HTTP/WebSocket)
2. **Phoenix** → Processes request via LiveView or API
3. **Application Layer** → Uses Neo4j driver (Boltx) to execute Cypher queries
4. **Neo4j** → Returns graph data
5. **Phoenix** → Renders response to client

### Asset Pipeline

1. **TypeScript** (`assets/js/app.ts`) → Compiled by Bun
2. **Tailwind CSS** (`assets/css/app.css`) → Processed by Bun/Tailwind
3. **Output** → `priv/static/assets/` (served by Phoenix)

## Prerequisites

- Docker and Docker Compose installed
- For local development (optional): Elixir 1.14+, Bun runtime

## Docker Compose Configuration

### Services

#### Neo4j Service

- **Image**: `neo4j:5-community`
- **Ports**: 
  - `7474` (HTTP/Browser interface)
  - `7687` (Bolt protocol)
- **Health Check**: HTTP check on port 7474
- **Volumes**: Persistent data and logs
- **Credentials**: `neo4j/password` (change in production!)

#### Phoenix App Service

- **Build**: Multi-stage Dockerfile
- **Port**: `4000`
- **Depends on**: Neo4j (waits for health check)
- **Volumes**: 
  - Source code (for hot-reload)
  - Build artifacts
  - Dependencies cache
- **Environment Variables**:
  - `NEO4J_URL=bolt://neo4j:7687` (uses Docker service name)
  - `NEO4J_USER=neo4j`
  - `NEO4J_PASSWORD=password`
  - `MIX_ENV=dev`

### Network Configuration

All services run on the `dnd_network` bridge network, allowing:
- Service name resolution (`neo4j` resolves to Neo4j container)
- Isolated network from host
- Easy port mapping to host

## TypeScript Setup

### Configuration

TypeScript is configured in `tsconfig.json` with:
- **Strict mode enabled** - Catches errors at compile time
- **Target**: ES2017+ (compatible with Phoenix LiveView)
- **Module resolution**: Node-style for compatibility

### Type Definitions

Phoenix libraries have type definitions in `assets/js/phoenix.d.ts`:
- `phoenix` - Socket, Channel, Presence types
- `phoenix_html` - HTML form helpers
- `phoenix_live_view` - LiveSocket types

### Converting JavaScript to TypeScript

The main entry point `assets/js/app.ts` includes:
- Type-safe imports
- Proper null checking for DOM elements
- Type annotations for Phoenix components

## Bun Integration

### Why Bun?

- **Native TypeScript support** - No transpilation step needed
- **Fast installs** - 10-20x faster than npm/yarn
- **Fast builds** - Native bundler outperforms esbuild
- **Tailwind compatibility** - Excellent PostCSS support

### Build Process

Build scripts are in `package.json`:
- `bun run build` - Production build (minified)
- `bun run watch` - Development build (watch mode)
- `bun run typecheck` - Type checking only

The build script (`assets/build.ts`) uses:
- **Bun.build()** - Native bundler for JavaScript/TypeScript
- **Tailwind CLI** - Via `bunx tailwindcss` for CSS

### Asset Compilation

```bash
# Development (watch mode)
cd assets
bun run watch

# Production build
cd assets
bun run build

# Or use Mix task (calls Bun)
mix assets.deploy
```

## Network Configuration & Troubleshooting

### Phoenix Binding

Phoenix is configured to bind to `0.0.0.0` (all interfaces) in `config/dev.exs`:
```elixir
http: [ip: {0, 0, 0, 0}, port: 4000]
```

This allows access from:
- Inside Docker containers
- Host machine (via port mapping)
- Other containers on the same network

### Neo4j Connection

The app connects to Neo4j using the Docker service name:
- **Docker Compose**: `bolt://neo4j:7687` (service name resolution)
- **Local development**: `bolt://localhost:7687` (if Neo4j runs on host)

Configuration in `config/config.exs`:
```elixir
config :dnd_app, DndApp.DB.Neo4j,
  url: System.get_env("NEO4J_URL") || "bolt://localhost:7687",
  username: System.get_env("NEO4J_USER") || "neo4j",
  password: System.get_env("NEO4J_PASSWORD") || "password"
```

### Common Connection Issues

#### Issue: "Connection refused" or "Connection reset"

**Symptoms**: Can't access http://localhost:4000

**Solutions**:
1. Check Phoenix is binding to `0.0.0.0`, not `127.0.0.1`
2. Verify port mapping in docker-compose.yml: `"4000:4000"`
3. Check if port 4000 is already in use: `lsof -i :4000`
4. Verify container is running: `docker ps | grep dnd-app`
5. Check container logs: `docker-compose logs dnd-app`

#### Issue: Neo4j connection fails

**Symptoms**: App starts but can't connect to Neo4j

**Solutions**:
1. Verify Neo4j is healthy: `docker-compose ps neo4j`
2. Check Neo4j logs: `docker-compose logs neo4j`
3. Verify service name in connection URL: `bolt://neo4j:7687`
4. Test connection from container: `docker-compose exec dnd-app sh -c "echo 'RETURN 1' | nc neo4j 7687"`
5. Verify environment variables in docker-compose.yml

#### Issue: Assets not loading

**Symptoms**: CSS/JS files return 404

**Solutions**:
1. Build assets: `docker-compose exec dnd-app sh -c "cd assets && bun run build"`
2. Check assets exist: `docker-compose exec dnd-app ls -la priv/static/assets/`
3. Verify volume mounts in docker-compose.yml
4. Restart container: `docker-compose restart dnd-app`

## Development Workflow

### Starting Development

```bash
# Start all services
docker-compose up

# Start in background
docker-compose up -d

# View logs
docker-compose logs -f dnd-app

# Stop services
docker-compose down
```

### Hot Reload

Phoenix supports hot-reload for:
- Elixir code changes (automatic)
- Asset changes (run `bun run watch` in assets directory)
- Template changes (automatic)

For asset hot-reload in Docker:
```bash
# Option 1: Run watcher in container
docker-compose exec dnd-app sh -c "cd assets && bun run watch"

# Option 2: Run watcher locally (if Bun is installed)
cd assets
bun run watch
```

### Running Commands in Container

```bash
# Run Mix tasks
docker-compose exec dnd-app mix test
docker-compose exec dnd-app mix format

# Run IEx console
docker-compose exec dnd-app iex -S mix

# Build assets
docker-compose exec dnd-app sh -c "cd assets && bun run build"
```

## Neo4j Integration

### Local Development (Docker)

When using Docker Compose, Neo4j is automatically configured and connected.

### Using Existing Neo4j Container

If you have an existing Neo4j container:

1. Remove Neo4j service from docker-compose.yml
2. Connect Phoenix to existing container:
   ```yaml
   environment:
     - NEO4J_URL=bolt://host.docker.internal:7687  # Mac/Windows
     # OR
     - NEO4J_URL=bolt://172.17.0.1:7687  # Linux (Docker bridge IP)
   ```

### Neo4j Aura (Cloud)

For production or cloud Neo4j:

```yaml
environment:
  - NEO4J_URL=bolt+ssc://your-instance.neo4j.io:7687
  - NEO4J_USER=neo4j
  - NEO4J_PASSWORD=your-password
```

Ensure SSL is enabled in `config/runtime.exs` for production.

### Neo4j Browser

Access Neo4j Browser at http://localhost:7474:
- Username: `neo4j`
- Password: `password` (or your configured password)

## Production Deployment

### Building Production Image

```bash
# Build image
docker build -t dnd-app:latest .

# Run container
docker run -d \
  --name dnd-app \
  -p 4000:4000 \
  -e MIX_ENV=prod \
  -e SECRET_KEY_BASE=your-secret-key \
  -e NEO4J_URL=bolt://your-neo4j:7687 \
  -e NEO4J_USER=neo4j \
  -e NEO4J_PASSWORD=your-password \
  dnd-app:latest
```

### Environment Variables

Required for production:
- `SECRET_KEY_BASE` - Generate with `mix phx.gen.secret`
- `NEO4J_URL` - Neo4j connection URL
- `NEO4J_USER` - Neo4j username
- `NEO4J_PASSWORD` - Neo4j password
- `PHX_HOST` - Your domain name
- `PORT` - Port to bind (default: 4000)

## GraphQL Codegen (Future)

When Ash Framework and GraphQL are integrated:

```bash
# Generate TypeScript types from GraphQL schema
cd assets
bun run codegen

# Watch mode (regenerates on schema changes)
bun run codegen:watch
```

This provides end-to-end type safety: Neo4j → Ash → GraphQL → TypeScript.

## Troubleshooting

### Container Won't Start

1. Check logs: `docker-compose logs dnd-app`
2. Verify Dockerfile syntax: `docker build -t test .`
3. Check resource limits (memory/CPU)
4. Verify all required files are present

### Build Failures

1. **TypeScript errors**: Run `bun run typecheck` locally
2. **Asset build failures**: Check Bun is installed in container
3. **Tailwind errors**: Verify tailwind.config.js syntax

### Performance Issues

1. Use volume caching (already configured in docker-compose.yml)
2. Pre-build assets in Dockerfile (already done)
3. Use multi-stage builds to reduce image size (already done)

## Additional Resources

- [Phoenix Deployment Guide](https://hexdocs.pm/phoenix/deployment.html)
- [Neo4j Docker Documentation](https://neo4j.com/developer/docker/)
- [Bun Documentation](https://bun.sh/docs)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/)

## Quick Reference

```bash
# Start services
docker-compose up

# Stop services
docker-compose down

# Rebuild and start
docker-compose up --build

# View logs
docker-compose logs -f

# Run commands
docker-compose exec dnd-app mix <command>

# Access Neo4j Browser
open http://localhost:7474

# Access Phoenix app
open http://localhost:4000
```

