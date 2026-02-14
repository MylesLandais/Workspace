# Imageboard Monitoring - DevOps Recovery Tools

## Overview

These scripts are designed for system recovery and operational monitoring of the imageboard monitoring system. They follow DevOps best practices with clear, actionable output and safe defaults.

## Scripts

### 1. trigger_catalog_scan.py

**Purpose:** Manually trigger catalog scanning and queue matching threads (for recovery scenarios).

**When to use:**
- After system restart or crash recovery
- When queue depth is unexpectedly low
- Before adding new keywords to validate matches
- When orchestrator is not functioning normally

**Usage:**

```bash
# Basic: Scan and queue all matching threads
python3 trigger_catalog_scan.py

# Dry run: See what would be queued without actually queueing
python3 trigger_catalog_scan.py --dry-run

# Limit to 20 threads maximum (prevents queue overload)
python3 trigger_catalog_scan.py --max-threads 20

# Only queue threads with 50+ replies (high activity)
python3 trigger_catalog_scan.py --min-replies 50

# Scan different board
python3 trigger_catalog_scan.py --board s

# Combined filters
python3 trigger_catalog_scan.py --max-threads 10 --min-replies 100 --dry-run
```

**Output:**
- Catalog fetch time
- Number of matching threads
- Sample of matched threads
- Queue depth before/after
- Filtering summary

**Keywords (default):**
`irl`, `face`, `celeb`, `JJ`, `girl`, `girls`, `feet`, `cel`, `panties`, `gooning`, `goon`, `zoomers`, `goddess`, `built`, `ss`, `actresses`

---

### 2. monitor_imageboard_health.py

**Purpose:** Monitor system health and alert on performance issues.

**When to use:**
- Continuous monitoring during recovery
- Periodic health checks
- Performance troubleshooting
- Pre-deployment validation

**Usage:**

```bash
# One-time health check
python3 monitor_imageboard_health.py

# Continuous monitoring (update every 10 seconds)
python3 monitor_imageboard_health.py --watch

# Custom update interval (30 seconds)
python3 monitor_imageboard_health.py --watch --interval 30

# Custom thresholds
python3 monitor_imageboard_health.py --max-queue 50 --max-cpu 70 --max-memory 512

# Combined monitoring
python3 monitor_imageboard_health.py --watch --interval 15 --max-queue 75
```

**Output:**
- **Queue Status:** Current depth, comparison to threshold
- **Collection Stats:** Thread count, image count, alerts
- **Container Health:** CPU and memory for each monitored container
- **Overall Status:** HEALTHY or ISSUES DETECTED

**Default Thresholds:**
- Max queue depth: 100
- Max CPU: 80%
- Max memory: 1024 MB
- Max monitored threads: 500

**Monitored Containers:**
- `imageboard_orchestrator`
- `imageboard_worker`
- `imageboard_dashboard`
- `imageboard_metrics_collector`

---

## Recovery Scenarios

### Scenario 1: System Restart

After restarting docker compose, queue needs replenishing:

```bash
# Check current state
python3 monitor_imageboard_health.py

# Trigger catalog scan if queue is low
python3 trigger_catalog_scan.py --max-threads 30

# Monitor as worker processes
python3 monitor_imageboard_health.py --watch
```

### Scenario 2: Queue Buildup Prevention

Monitor continuously and set aggressive thresholds:

```bash
# Monitor with low queue threshold (catch issues early)
python3 monitor_imageboard_health.py --watch --interval 5 --max-queue 50
```

If queue exceeds threshold, take action:
```bash
# Check what's in the queue
docker exec cache.jupyter.dev.local valkey-cli LRANGE queue:monitors 0 -10

# Increase worker scale or pause orchestrator temporarily
docker compose scale imageboard_worker=2
# or
docker pause imageboard_orchestrator
```

### Scenario 3: Performance Investigation

Identify bottlenecks during high load:

```bash
# Run health check with detailed output
python3 monitor_imageboard_health.py

# Check container logs for errors
docker logs imageboard_worker --tail=100

# Monitor specific container over time
watch -n 2 'docker stats --no-stream imageboard_worker'
```

### Scenario 4: Adding New Keywords

Validate keyword changes before deployment:

```bash
# Dry run with new keywords (edit KEYWORDS list first)
# Edit trigger_catalog_scan.py KEYWORDS list, then:
python3 trigger_catalog_scan.py --dry-run --max-threads 100

# Review output, adjust keywords, repeat
# Once satisfied:
python3 trigger_catalog_scan.py --max-threads 20
```

---

## Running Scripts

### Option 1: On Host System

If Python 3 + dependencies are available:

```bash
# Install dependencies
pip install redis requests

# Run scripts
python3 trigger_catalog_scan.py
python3 monitor_imageboard_health.py
```

### Option 2: Via Docker (Host has docker but no Python)

```bash
# Install dependencies in container
docker run --rm --network host \
  -v /home/warby/Workspace/jupyter/trigger_catalog_scan.py:/app/trigger_catalog_scan.py \
  python:3-alpine sh -c \
  "pip install redis requests && cd /app && python3 trigger_catalog_scan.py"
```

### Option 3: Within Existing Container

Use existing containers that have dependencies:

```bash
# Orchestrator or worker containers
docker compose -f docker-compose-otel.yml exec imageboard_orchestrator \
  python3 -c "import sys; sys.path.insert(0, '/home/warby/Workspace/jupyter'); exec(open('trigger_catalog_scan.py').read())"
```

---

## Best Practices

1. **Always use --dry-run first** before queueing many threads
2. **Set max-threads limit** (e.g., 20-30) to prevent queue overload
3. **Monitor continuously** during recovery: `python3 monitor_imageboard_health.py --watch`
4. **Check logs** when alerts occur
5. **Use min-replies filter** to prioritize active threads
6. **Review keywords** regularly to reduce false positives

---

## Troubleshooting

### "redis-cli: command not found"

The health monitor uses docker exec to check queue depth. Ensure:
- Redis/Valkey container is running
- Container is named with 'redis' or 'valkey'

### "No such file or directory: 'docker'"

Run health monitor on host system, not inside container (it needs docker CLI).

### Queue depth always 0

Check Redis connection:
```bash
docker exec <redis-container> redis-cli PING
```

Check queue name matches worker expectation (`queue:monitors`).

### High CPU alerts

- Check worker processing rate vs new thread arrival rate
- Consider scaling workers: `docker compose scale imageboard_worker=2`
- Verify no infinite loops in worker code

### High memory alerts

- Check image cache size: `du -sh cache/imageboard/shared_images`
- Review image deduplication working
- Consider archival or cleanup of old threads
