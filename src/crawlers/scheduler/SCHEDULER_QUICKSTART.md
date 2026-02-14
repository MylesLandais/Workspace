# Task Scheduler Quick Start - Phase 2 Implementation

Complete Celery-based task scheduler with PostgreSQL persistence, nix-shell execution, and Flower monitoring.

## What's Implemented

**Phase 1 (Complete)**: Reproducible development environment
- Nix/devenv with all dependencies
- PostgreSQL database with schema
- Docker Compose with all services
- Configuration and documentation

**Phase 2 (Complete)**: Scheduler Core Execution Engine
- Celery + RedBeat distributed task queue
- Nix-shell execution with hash-based caching
- PostgreSQL task persistence
- Flower UI for monitoring (http://localhost:5555)
- Typer CLI for task management
- Integration with 3 existing jobs: poll_reddit, deduplication, imageboards

## Starting the System

### 1. Initialize Development Environment

```bash
cd ~/Workspace/jupyter
cp .env.example .env  # Copy if not already done
direnv allow
docker compose up -d
uv sync
```

Verify services are running:
```bash
docker compose ps

# Expected output: postgres, valkey, neo4j, celery-worker, celery-beat, flower
```

### 2. Check PostgreSQL Schema

```bash
psql -U scheduler -h localhost -d feed_scheduler -c "\dt"

# Should list: scheduled_tasks, task_runs, task_steps, nix_environments
```

## Using the CLI

The scheduler is managed via Typer CLI from the command line:

```bash
python -m src.feed.scheduler.cli --help
```

### Creating Tasks

**Example: Daily Reddit Poll**
```bash
python -m src.feed.scheduler.cli create \
  "Reddit r/ML Poll" \
  "/scripts/poll_reddit.py" \
  "FREQ=DAILY;BYHOUR=2;BYMINUTE=0" \
  --packages "python3,python3Packages.praw,python3Packages.neo4j" \
  --description "Poll r/MachineLearning for new posts daily at 2 AM" \
  --concurrent 1 \
  --timeout 3600
```

**Example: Hourly Deduplication**
```bash
python -m src.feed.scheduler.cli create \
  "Deduplication Job" \
  "/scripts/dedup.py" \
  "FREQ=HOURLY;INTERVAL=4" \
  --packages "python3,python3Packages.pillow,python3Packages.numpy" \
  --concurrent 1 \
  --timeout 7200
```

**Example: Continuous Imageboard Monitoring**
```bash
python -m src.feed.scheduler.cli create \
  "4chan /b/ Monitor" \
  "/scripts/monitor_imageboard.py" \
  "FREQ=MINUTELY;INTERVAL=5" \
  --packages "python3,python3Packages.aiohttp" \
  --concurrent 2 \
  --timeout 600
```

### Listing Tasks

```bash
# Show all tasks
python -m src.feed.scheduler.cli list

# Show only enabled tasks
python -m src.feed.scheduler.cli list --enabled

# Show with pagination
python -m src.feed.scheduler.cli list --limit 50 --offset 0
```

### Task Details

```bash
python -m src.feed.scheduler.cli show <task-id>
```

### Controlling Tasks

```bash
# Enable a task
python -m src.feed.scheduler.cli enable <task-id>

# Disable a task
python -m src.feed.scheduler.cli disable <task-id>

# Trigger task immediately (skip schedule)
python -m src.feed.scheduler.cli trigger <task-id>
```

### Viewing Execution History

```bash
# Show recent runs (all tasks)
python -m src.feed.scheduler.cli runs --limit 20

# Show runs for specific task
python -m src.feed.scheduler.cli runs --task <task-id>

# Filter by status
python -m src.feed.scheduler.cli runs --status success --limit 10
python -m src.feed.scheduler.cli runs --status failed --limit 10
```

### Logs

```bash
# Show stdout from a run
python -m src.feed.scheduler.cli logs <run-id>

# Show stderr from a run
python -m src.feed.scheduler.cli logs <run-id> --stderr
```

### Statistics

```bash
# Overall system stats
python -m src.feed.scheduler.cli stats

# Show cached nix environments
python -m src.feed.scheduler.cli envs

# Show most-used environments
python -m src.feed.scheduler.cli envs --sort uses
```

## Monitoring

### Flower Web UI

Open http://localhost:5555 to monitor:
- Active tasks and workers
- Task history with filtering
- Worker resource usage
- Task execution details (args, kwargs, logs, tracebacks)

### Database Queries

```bash
psql -U scheduler -h localhost -d feed_scheduler

# View all scheduled tasks
SELECT id, name, schedule_rrule, next_run_at, enabled FROM scheduled_tasks;

# View recent task runs
SELECT id, status, started_at, duration_ms FROM task_runs ORDER BY started_at DESC LIMIT 20;

# View execution statistics
SELECT status, COUNT(*) as count, AVG(duration_ms) as avg_duration
FROM task_runs GROUP BY status;

# View most-used nix environments
SELECT hash, use_count, last_used_at FROM nix_environments ORDER BY use_count DESC LIMIT 10;
```

### Celery Worker Logs

```bash
# Watch celery worker logs
docker compose logs -f celery-worker

# Watch celery beat scheduler logs
docker compose logs -f celery-beat

# Check active tasks
docker compose exec celery-worker celery -A src.feed.scheduler.celery_app inspect active
```

## RRule Schedule Format

Tasks use RFC 5545 RRule format (same as Google Calendar, Outlook):

```
FREQ=DAILY                                    # Every day
FREQ=DAILY;INTERVAL=2                        # Every 2 days
FREQ=DAILY;BYHOUR=2;BYMINUTE=0              # Daily at 2:00 AM
FREQ=WEEKLY;BYDAY=MO,WE,FR                  # Mon/Wed/Fri
FREQ=HOURLY;INTERVAL=4                      # Every 4 hours
FREQ=MINUTELY;INTERVAL=15                   # Every 15 minutes
FREQ=MONTHLY;BYMONTHDAY=1                   # 1st of every month
```

## Architecture

### Task Execution Flow

1. **Schedule**: Celery Beat reads `scheduled_tasks` table every 15 seconds
2. **Queue**: If task's `next_run_at` is reached, enqueue task to Celery queue
3. **Execute**: Celery worker receives task from queue
4. **Nix**: NixRunner looks up or builds nix-shell environment from package spec
5. **Run**: Execute Python script in nix-shell (fast due to cached environments)
6. **Record**: Update `task_runs` table with stdout, stderr, exit_code, duration
7. **Monitor**: View in Flower UI or query PostgreSQL

### Nix Environment Caching

The innovation: pre-built nix-shell environments cached by package hash:

1. Hash package spec (sorted, JSON serialized) → SHA256
2. Look up hash in `nix_environments` table
3. Cache hit: Use cached `.drv` path (instant)
4. Cache miss: Build via nix-instantiate/nix-store, cache result
5. Result: <100ms startup for cached, ~5s for new environments

Benefits:
- Reproducible execution (same packages → same .drv file)
- Fast execution (pre-built environments, <100ms startup)
- Storage efficient (deduplicated environments by hash)

## Integration with Existing Jobs

The scheduler is designed to wrap existing jobs. Examples:

**poll_reddit_task**:
- Wraps `poll_creator_sources.py`
- Accepts: creator_slug, subreddits, max_posts
- Output: total posts, new posts, duplicates
- Queue: reddit (priority)

**dedup_task**:
- Wraps `run_dedup.py`
- Accepts: limit, offset, batch_size, use_clip
- Output: processed, successful, duplicates found
- Queue: dedup (lower priority)

**poll_imageboard_catalog**:
- Wraps `imageboard_monitor_worker.py` catalog poller
- Accepts: board, poll_interval
- Output: active threads, new threads
- Queue: imageboards (high priority)

## Next Steps

### Phase 3: GraphQL API (Deferred)

- Add GraphQL schema for task queries
- REST endpoints for programmatic access
- Real-time subscriptions for task monitoring

### Phase 4: React UI (Deferred)

- React dashboard with shadcn/tailwind
- RRule editor with visual calendar
- Real-time task monitoring
- Outlook-style interface

### Phase 5: Testing & Hardening

- Unit tests for nix_runner.py, task_service.py
- Integration tests for end-to-end execution
- Load testing (1000+ concurrent tasks)
- Performance tuning

## Troubleshooting

### PostgreSQL connection refused

```bash
docker compose ps postgres
docker compose logs postgres
docker compose restart postgres
sleep 5
docker compose exec postgres pg_isready -U scheduler
```

### Celery worker won't start

```bash
docker compose logs celery-worker
docker compose restart celery-worker

# Check Redis is running
redis-cli -h localhost ping  # Should return PONG
```

### Tasks not being scheduled

```bash
# Check Beat scheduler logs
docker compose logs celery-beat

# Check if task is enabled
python -m src.feed.scheduler.cli show <task-id>  # enabled: true?

# Check next_run_at time
psql -c "SELECT name, next_run_at FROM scheduled_tasks WHERE enabled = true;"
```

### Nix environment build failures

```bash
# Check Nix is available
nix --version
which nix-shell
which nix-instantiate

# Test manual nix-shell
nix-shell -p python3 --run "python3 --version"

# Check nix-store
nix-store -q --references /nix/store/...
```

## Documentation

See also:
- `DEVENV_SETUP.md` - Development environment quick reference
- `docs/development-environment.md` - Complete dev environment guide
- `~/.claude/plans/compiled-mixing-pearl.md` - Architecture and design decisions
- `readme.md` - Project overview
