# Quick Development Environment Setup

Complete reproducible environment with one command.

## One-Liner Setup

```bash
cd ~/Workspace/jupyter && cp .env.example .env && direnv allow && docker compose up -d && uv sync
```

## Step-by-Step Setup

### 1. Enable Nix Flakes (First Time Only)

```bash
mkdir -p ~/.config/nix
echo "experimental-features = nix-command flakes" >> ~/.config/nix/nix.conf
```

### 2. Enter Development Shell

```bash
cd ~/Workspace/jupyter

# With direnv (automatic):
direnv allow

# Or manually:
devenv shell
```

**What you get:**
- Python 3.11 + all dependencies
- PostgreSQL client tools
- Docker Compose
- Node.js, Git, Make, uv
- Everything needed for development

### 3. Verify Nix Setup

```bash
python --version      # Python 3.11
postgres --version    # PostgreSQL 16
node --version        # Node.js
uv --version          # Python package manager
```

### 4. Start Docker Services

```bash
# Copy environment config
cp .env.example .env

# Start all services
docker compose up -d

# Wait for PostgreSQL to be ready (takes 10-15 seconds)
sleep 15

# Verify all services
docker compose ps
```

**Expected output:**
```
CONTAINER ID   NAMES                          STATUS
...
postgres.jupyter.dev.local     Up (healthy)
valkey.jupyter.dev.local       Up (healthy)
neo4j.jupyter.dev.local        Up
celery-worker.dev.local        Up
celery-beat.dev.local          Up
flower.dev.local               Up
```

### 5. Install Python Dependencies

```bash
uv sync
```

### 6. Verify Database

```bash
psql -U scheduler -h localhost -d feed_scheduler -c "\dt"
```

**Expected output:** (tables listed)
```
public | scheduled_tasks      | table | scheduler
public | task_runs            | table | scheduler
public | task_steps           | table | scheduler
public | nix_environments     | table | scheduler
```

## Minimal Start (Database Only)

If you don't need all services:

```bash
docker compose up -d postgres valkey
uv sync
```

## Service Access

| Service | URL/Port | Credentials |
|---------|----------|-------------|
| JupyterLab | http://localhost:8888 | (no auth) |
| Flower (Celery UI) | http://localhost:5555 | - |
| PostgreSQL | localhost:5432 | scheduler / localpassword |
| Neo4j | http://localhost:7474 | neo4j / localpassword |
| MinIO S3 | http://localhost:9000 | minioadmin / minioadmin |
| Redis | localhost:6379 | (no password) |

## Quick Commands

### Task Scheduler CLI

```bash
# Create a task
python -m src.feed.scheduler.cli create \
  --name "My Task" \
  --script-path "/tmp/test.py" \
  --schedule-rrule "FREQ=DAILY" \
  --nix-packages "python3"

# List tasks
python -m src.feed.scheduler.cli list

# Trigger task immediately
python -m src.feed.scheduler.cli trigger <task-id>

# View runs
python -m src.feed.scheduler.cli runs --limit 10
```

### Database Queries

```bash
# Connect to PostgreSQL
psql -U scheduler -h localhost -d feed_scheduler

# View task runs
SELECT id, status, started_at, duration_ms FROM task_runs ORDER BY started_at DESC LIMIT 10;

# Count tasks by status
SELECT status, COUNT(*) FROM task_runs GROUP BY status;

# View nix environments
SELECT hash, use_count, last_used_at FROM nix_environments;
```

### Docker Management

```bash
# View all services
docker compose ps

# View logs
docker compose logs -f celery-worker
docker compose logs -f postgres

# Restart a service
docker compose restart celery-worker

# Stop all services
docker compose down

# Remove everything (data included)
docker compose down -v
```

### Testing

```bash
# Run tests
pytest tests/scheduler/ -v

# With coverage
pytest tests/ --cov=src/feed/scheduler

# Integration tests
pytest tests/integration/test_scheduler_e2e.py -v
```

## Development Workflow

### Start Your Day

```bash
# Enter shell
devenv shell

# Start services
docker compose up -d

# Monitor
docker compose logs -f

# In another terminal:
python -m src.feed.scheduler.cli list
```

### End Your Day

```bash
# Stop services (data persisted)
docker compose down

# Or exit devenv shell
exit
```

## Troubleshooting

### Python module not found

```bash
# Ensure you're in the devenv shell
devenv shell

# Sync dependencies
uv sync
```

### PostgreSQL connection refused

```bash
# Check if service is running
docker compose ps postgres

# Restart it
docker compose restart postgres

# Wait for health
docker compose exec postgres pg_isready -U scheduler -d feed_scheduler
```

### Celery not connecting to Redis

```bash
# Check Redis is running
docker compose ps valkey

# Test connection
redis-cli -h localhost ping
# Should return: PONG
```

### Port already in use

```bash
# Find and kill process
lsof -ti:5432 | xargs kill -9

# Or check what's using it
lsof -i:5432
```

### Slow nix operations

```bash
# Clear cache and refresh
nix flake update --refresh

# Or just update once
nix flake update
```

## For CI/CD

```bash
# Build pure environment
nix build .#devShell.x86_64-linux

# Run in pure environment
nix develop --command bash
```

## Environment Files

- `.env.example` - Sample environment variables (template)
- `.env` - Your local environment (create from .env.example, not committed)
- `.devenv.flake.nix` - Auto-generated devenv config (don't edit)
- `devenv.nix` - Main devenv configuration (edit to add packages)
- `devenv.lock` - Locked devenv versions
- `flake.lock` - Locked Nix inputs
- `docker-compose.yml` - Docker service definitions

## Documentation

For detailed information, see:

- `docs/development-environment.md` - Complete dev environment guide
- `~/.claude/plans/compiled-mixing-pearl.md` - Architecture plan
- `pyproject.toml` - Python dependencies
- `devenv.nix` - Nix packages and services
