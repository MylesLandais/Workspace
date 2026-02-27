# Reproducible Development Environment

This project uses Nix and devenv for a completely reproducible development environment across Linux and macOS.

## Quick Start

### Prerequisites

- Nix (with flakes support enabled)
- Docker and Docker Compose
- PostgreSQL client tools (optional, included in devenv)

### Installation

1. **Enable Nix flakes** (if not already enabled):

```bash
mkdir -p ~/.config/nix
echo "experimental-features = nix-command flakes" >> ~/.config/nix/nix.conf
```

2. **Enter the development shell**:

```bash
cd ~/Workspace/jupyter

# Using direnv (automatic on cd):
direnv allow

# Or manually:
nix flake update
devenv shell
```

3. **Install Python dependencies**:

```bash
# Using uv (recommended, faster):
uv sync

# Or using pip:
pip install -e .
```

4. **Start Docker services**:

```bash
# Copy .env if you haven't already
cp .env.example .env

# Start all services
docker compose up -d

# Verify services are running
docker compose ps

# Check PostgreSQL schema
psql -U scheduler -h localhost -d feed_scheduler -c "\dt"
```

## Environment Overview

### Development Shell (devenv)

The development shell includes:

- **Python 3.11** with all project dependencies
- **PostgreSQL 16** client tools
- **Docker Compose** for service orchestration
- **Node.js** for potential frontend work
- **uv** for fast Python dependency management
- **Make**, **Git**, and common development tools

### Docker Services

Services managed by Docker Compose:

| Service | Port | Access | Purpose |
|---------|------|--------|---------|
| JupyterLab | 8888 | http://localhost:8888 | Interactive notebook environment |
| PostgreSQL | 5432 | postgresql://scheduler:localpassword@localhost:5432/feed_scheduler | Task scheduler database |
| Neo4j | 7687 | bolt://neo4j:7687 | Knowledge graph database |
| Valkey/Redis | 6379 | redis://localhost:6379 | Cache and task queue |
| MinIO | 9000 | http://localhost:9000 | S3-compatible object storage |
| Flower | 5555 | http://localhost:5555 | Celery task monitoring |
| Celery Worker | - | - | Background task execution |
| Celery Beat | - | - | Task scheduling engine |

### Python Environment

All Python dependencies are specified in:

- `pyproject.toml` - Package configuration and main dependencies
- `devenv.nix` - Nix-managed Python and system packages

Key scheduler-specific packages:

- **Celery** - Distributed task queue
- **celery-redbeat** - Redis-based beat scheduler with RRule support
- **psycopg2** - PostgreSQL adapter
- **Typer** - CLI framework for task management
- **Flower** - Celery monitoring UI

## Common Workflows

### Running the Scheduler

1. **Start infrastructure**:

```bash
docker compose up -d postgres valkey redis celery-worker celery-beat flower
```

2. **Monitor tasks** (in browser):

Open http://localhost:5555 (Flower UI)

3. **Create and manage tasks** (CLI):

```bash
# Create a new scheduled task
python -m src.feed.scheduler.cli create \
  --name "Test Task" \
  --script-path "/tmp/test.py" \
  --schedule-rrule "FREQ=DAILY" \
  --nix-packages "python3"

# List all tasks
python -m src.feed.scheduler.cli list

# Trigger a task manually
python -m src.feed.scheduler.cli trigger <task-id>

# View recent runs
python -m src.feed.scheduler.cli runs
```

### Database Operations

```bash
# Connect to PostgreSQL
psql -U scheduler -h localhost -d feed_scheduler

# List tables
\dt

# View recent task runs
SELECT id, task_id, status, started_at, duration_ms FROM task_runs ORDER BY started_at DESC LIMIT 10;

# Apply migrations
psql -U scheduler -h localhost -d feed_scheduler < src/feed/storage/migrations/postgres/001_scheduler_schema.sql
```

### Debugging

```bash
# Celery worker logs
docker compose logs -f celery-worker

# Celery beat logs
docker compose logs -f celery-beat

# PostgreSQL logs
docker compose logs -f postgres

# Check Flower status
docker compose exec celery-worker celery -A src.feed.scheduler.celery_app inspect active
```

### Testing

```bash
# Run unit tests
pytest tests/scheduler/ -v

# Run integration tests
pytest tests/integration/ -v

# Run with coverage
pytest tests/ --cov=src/feed/scheduler --cov-report=html
```

## Reproducibility

### For New Developers

1. Clone the repository
2. Install Nix with flakes support
3. Run `direnv allow` or `nix flake update && devenv shell`
4. All dependencies are automatically available

### For CI/CD

```bash
# The environment is completely reproducible:
nix flake update
nix build .#devShell.x86_64-linux
```

### Lock Files

- `devenv.lock` - Pinned devenv versions (managed by devenv)
- `flake.lock` - Pinned Nixpkgs and input versions (use `nix flake update` to refresh)

## Multi-System Support

The Nix configuration supports multiple systems:

- `x86_64-linux` (Linux Intel/AMD)
- `aarch64-linux` (Linux ARM)
- `x86_64-darwin` (macOS Intel)
- `aarch64-darwin` (macOS ARM/Apple Silicon)

To build for a different system:

```bash
nix build .#devShell.aarch64-darwin
```

## Environment Variables

### Essential (.env)

```bash
# PostgreSQL
POSTGRES_URL=postgresql://scheduler:localpassword@localhost:5432/feed_scheduler

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1

# Neo4j
NEO4J_URI=bolt://neo4j:7687
NEO4J_PASSWORD=localpassword

# Redis
VALKEY_HOST=localhost
VALKEY_PORT=6379
```

Copy `.env.example` to `.env` and customize as needed.

## Troubleshooting

### Nix Issues

**Problem**: "experimental-features = nix-command flakes" error

**Solution**:
```bash
mkdir -p ~/.config/nix
echo "experimental-features = nix-command flakes" >> ~/.config/nix/nix.conf
```

**Problem**: `nix flake update` is slow

**Solution**: Use `--refresh` flag to bypass cache:
```bash
nix flake update --refresh
```

### Docker Issues

**Problem**: Port already in use

**Solution**:
```bash
# Find and kill process using the port
lsof -ti:5432 | xargs kill -9

# Or use different port
docker compose -f docker-compose.yml.local up -d
```

**Problem**: PostgreSQL won't start

**Solution**:
```bash
# Remove old volume
docker volume rm jupyter_postgres_data

# Restart services
docker compose restart postgres
```

### Python/Celery Issues

**Problem**: Module not found errors

**Solution**:
```bash
# Ensure you're in the devenv shell
devenv shell

# Reinstall dependencies
uv sync --refresh
```

**Problem**: Celery worker won't connect to broker

**Solution**:
```bash
# Check Redis is running
docker compose ps valkey

# Verify connection
redis-cli -h localhost ping
# Should return: PONG
```

## Documentation References

- [Nix Package Manager](https://nixos.org/manual/nix/)
- [devenv Documentation](https://devenv.sh/)
- [Celery Documentation](https://docs.celeryproject.io/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Docker Compose Reference](https://docs.docker.com/compose/)

## Next Steps

1. Review the task scheduler architecture in the plan file:
   ```bash
   cat ~/.claude/plans/compiled-mixing-pearl.md
   ```

2. Start the infrastructure:
   ```bash
   docker compose up -d
   ```

3. Verify everything works:
   ```bash
   python -m src.feed.scheduler.cli list
   ```

4. Begin implementing Phase 2 (Scheduler Core)
