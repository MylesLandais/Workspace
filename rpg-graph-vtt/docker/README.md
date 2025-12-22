# Docker Configuration for RPG Graph VTT

This directory contains Docker configuration files for building, testing, and deploying the RPG Graph VTT service.

## Quick Start

### Prerequisites

- Docker and Docker Compose installed
- Neo4j database (cloud or local)
- Environment variables configured

### Setup

1. **Copy environment file:**
   ```bash
   cd rpg-graph-vtt/docker
   cp .env.example .env
   ```

2. **Edit `.env` with your Neo4j credentials:**
   ```bash
   NEO4J_URI=neo4j+s://your-instance.databases.neo4j.io
   NEO4J_USERNAME=neo4j
   NEO4J_PASSWORD=your-password
   ```

3. **Build and start:**
   ```bash
   make build
   make up
   ```

4. **Access the service:**
   - Web UI: http://localhost:8000
   - API Docs: http://localhost:8000/docs
   - API: http://localhost:8000/api/characters

## Using Make Commands

```bash
make help      # Show all available commands
make build     # Build Docker image
make up        # Start service
make up-db     # Start with local Neo4j
make down      # Stop service
make logs      # View logs
make shell     # Open shell in container
make test      # Run tests
make validate  # Check if service is running
make clean     # Remove containers and volumes
```

## Using Docker Compose Directly

```bash
# Build
docker compose build

# Start service
docker compose up -d

# Start with local Neo4j
docker compose --profile local-db up -d

# View logs
docker compose logs -f rpg-graph-vtt

# Stop
docker compose down
```

## Local Development with Neo4j

To run with a local Neo4j instance:

```bash
# Start both service and Neo4j
make up-db

# Access Neo4j Browser
# http://localhost:7474
# Username: neo4j
# Password: (from .env file, default: changeme)
```

## Testing

### Manual Testing

```bash
# Check service health
curl http://localhost:8000/api/characters

# Check API docs
curl http://localhost:8000/docs
```

### Automated Tests

```bash
# Run tests in container
make test

# Or manually
docker compose exec rpg-graph-vtt pytest tests/ -v
```

## Production Deployment

### Building for Production

```bash
# Build with specific tag
docker compose build --no-cache

# Tag for registry
docker tag rpg-graph-vtt:latest your-registry/rpg-graph-vtt:latest

# Push to registry
docker push your-registry/rpg-graph-vtt:latest
```

### Environment Variables

Required environment variables:
- `NEO4J_URI` - Neo4j connection URI
- `NEO4J_PASSWORD` - Neo4j password

Optional:
- `NEO4J_USERNAME` - Neo4j username (default: neo4j)
- `NEO4J_DATABASE` - Database name (default: neo4j)

### Health Checks

The service includes health checks:
- HTTP endpoint: `GET /api/characters`
- Interval: 30 seconds
- Timeout: 10 seconds
- Retries: 3

## Troubleshooting

### Service Won't Start

1. Check logs:
   ```bash
   make logs
   ```

2. Verify environment variables:
   ```bash
   docker compose exec rpg-graph-vtt env | grep NEO4J
   ```

3. Test Neo4j connection:
   ```bash
   docker compose exec rpg-graph-vtt python -c "from rpg_graph_vtt.graph.connection import get_connection; conn = get_connection(); print('Connected:', conn.uri)"
   ```

### Port Already in Use

If port 8000 is already in use, modify `docker-compose.yml`:

```yaml
ports:
  - "8001:8000"  # Use port 8001 on host
```

### Database Connection Issues

1. Verify Neo4j is accessible from container
2. Check firewall rules
3. For cloud Neo4j, ensure IP whitelist includes container IP
4. Verify credentials in `.env` file

## File Structure

```
docker/
├── Dockerfile              # Service container definition
├── docker-compose.yml      # Service orchestration
├── .env.example           # Example environment file
├── entrypoint.sh          # Container startup script
├── Makefile               # Convenience commands
└── README.md              # This file
```

## Integration with NixOS

For NixOS systems, ensure Docker is properly configured:

```nix
# In your NixOS configuration
services.docker.enable = true;
virtualisation.docker.enable = true;
```

Then use the Docker commands as normal.

## Development Workflow

1. **Make changes** to code in `rpg-graph-vtt/`
2. **Rebuild** image: `make build`
3. **Restart** service: `make restart`
4. **Test** changes: `make validate`

For faster iteration, mount the code as a volume (see `docker-compose.yml` volumes section).

## Security Notes

- Never commit `.env` file with real credentials
- Use secrets management in production
- Keep Docker images updated
- Use non-root user in container (already configured)
- Enable HTTPS in production (use reverse proxy)



