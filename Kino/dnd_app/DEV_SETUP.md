# Local Development Setup Guide

This guide covers everything you need to get the D&D App running locally for development.

## Quick Start

If everything is already set up, just run:

```bash
cd dnd_app
./start.sh
```

Then open http://localhost:4000 in your browser.

## First Time Setup

### Prerequisites

1. **Elixir 1.14+** and **Erlang/OTP 24+**
   - Check: `elixir --version`
   - Install: https://elixir-lang.org/install.html

2. **Bun** (for asset compilation and TypeScript)
   - Check: `bun --version`
   - Install: https://bun.sh/docs/installation
   - Alternative: Use Docker Compose (see [DOCKER_DEPLOYMENT.md](DOCKER_DEPLOYMENT.md))

3. **Docker** (for Neo4j, optional if you have Neo4j installed locally)
   - Check: `docker --version`
   - Install: https://docs.docker.com/get-docker/
   - Recommended: Use Docker Compose for full setup (see [DOCKER_DEPLOYMENT.md](DOCKER_DEPLOYMENT.md))

4. **Neo4j Database**
   - Option 1: Run in Docker (recommended)
   - Option 2: Local installation
   - Option 3: Use Docker Compose (see [DOCKER_DEPLOYMENT.md](DOCKER_DEPLOYMENT.md))

### Setup Steps

1. **Clone the repository** (if not already done)

2. **Install dependencies:**
   ```bash
   cd dnd_app
   mix deps.get
   cd assets && bun install && cd ..
   ```
   
   **Note**: We use Bun instead of npm for faster installs and native TypeScript support.

3. **Start Neo4j:**
   ```bash
   docker run -d \
     --name neo4j-dnd \
     -p 7474:7474 \
     -p 7687:7687 \
     -e NEO4J_AUTH=neo4j/password \
     neo4j:5-community
   ```

4. **Verify setup:**
   ```bash
   bin/check
   ```
   This diagnostic script will check all prerequisites and report any issues.

5. **Start the server:**
   ```bash
   ./start.sh
   ```
   Or manually:
   ```bash
   mix phx.server
   ```

6. **Open in browser:** http://localhost:4000

## Diagnostic Script

The `bin/check` script quickly identifies setup issues:

```bash
cd dnd_app
bin/check
```

It checks:
- Elixir/Mix installation
- Dependencies (Elixir and Node.js)
- Code compilation
- Neo4j availability and connection
- Port 4000 availability

Run this first if you encounter any issues!

## Health Check Endpoint

Once the server is running, verify it's working:

```bash
curl http://localhost:4000/health
```

This returns JSON with status information:
- `status`: "ok" or "degraded"
- `phoenix`: Server status
- `neo4j`: Connection status
- `schema`: Database schema status

Example response:
```json
{
  "status": "ok",
  "phoenix": "running",
  "neo4j": "connected",
  "schema": {"status": "ready", "constraints": 4},
  "timestamp": "2024-01-01T12:00:00Z"
}
```

## Container Development

If you're using the `jupyter` container:

The `start.sh` script automatically detects if you're in a container or if the `jupyter` container is available and will use `docker exec` appropriately.

**Inside the container:**
```bash
docker exec -it jupyter bash
cd /workspace/dnd_app
./start.sh
```

**From host (script auto-detects):**
```bash
cd dnd_app
./start.sh  # Will use docker exec automatically if jupyter container exists
```

## Common Issues

### "Elixir/Mix not found"

**Problem:** Elixir is not installed or not in PATH.

**Solution:**
- Install Elixir: https://elixir-lang.org/install.html
- Or use the jupyter container if available

### "Neo4j connection failed"

**Problem:** Neo4j is not running or credentials are incorrect.

**Solutions:**
1. Check if Neo4j is running:
   ```bash
   docker ps | grep neo4j
   ```

2. Start Neo4j if not running:
   ```bash
   docker run -d --name neo4j-dnd -p 7474:7474 -p 7687:7687 -e NEO4J_AUTH=neo4j/password neo4j:5-community
   ```

3. Verify credentials in `config/config.exs` match your Neo4j setup

4. Test connection manually:
   ```bash
   docker exec neo4j-dnd cypher-shell -u neo4j -p password "RETURN 1"
   ```

### "Port 4000 already in use"

**Problem:** Another process is using port 4000.

**Solutions:**
1. Find and stop the process:
   ```bash
   lsof -i :4000
   # Kill the process ID shown
   ```

2. Or change the port in `config/dev.exs`:
   ```elixir
   http: [ip: {0, 0, 0, 0}, port: 4001]
   ```

### "Code has compilation errors"

**Problem:** Source code has errors or dependencies are outdated.

**Solutions:**
1. Check compilation errors:
   ```bash
   mix compile
   ```

2. Update dependencies:
   ```bash
   mix deps.get
   mix deps.compile
   ```

3. Clean and rebuild:
   ```bash
   mix clean
   mix compile
   ```

### "Dependencies not installed"

**Problem:** Elixir or Node.js dependencies are missing.

**Solutions:**
```bash
# Elixir dependencies
mix deps.get

# Node.js dependencies
cd assets && npm install && cd ..
```

## Development Workflow

1. **Start the server:**
   ```bash
   ./start.sh
   ```

2. **Make code changes** - Phoenix automatically recompiles and reloads

3. **Check server status:**
   ```bash
   curl http://localhost:4000/health
   ```

4. **Run diagnostics if issues arise:**
   ```bash
   bin/check
   ```

## Neo4j Browser

Access the Neo4j web interface at http://localhost:7474

- Username: `neo4j`
- Password: `password` (or whatever you set in docker run command)

## Additional Resources

- **Troubleshooting:** See `TROUBLESHOOTING.md` for detailed troubleshooting steps
- **Testing:** See `TESTING.md` for running tests
- **UAT Guide:** See `UAT_GUIDE.md` for user acceptance testing
- **Container Setup:** See `CONTAINER_SETUP.md` for container-specific setup

## Quick Reference

```bash
# Start server
./start.sh

# Run diagnostics
bin/check

# Check health
curl http://localhost:4000/health

# Run tests
mix test

# Format code
mix format

# Check compilation
mix compile
```

