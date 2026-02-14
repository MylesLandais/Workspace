# Imageboard Crawler - OTEL Monitoring

OpenTelemetry-based monitoring system for imageboard crawler with 4-hour monitoring sessions, conservative alerts, and data persistence for later analysis.

## Overview

This system provides:
- Real-time metrics collection via OpenTelemetry
- Prometheus + Pushgateway for metrics storage
- JSON exports for offline analysis
- Conservative alerting on critical issues
- Live console dashboard
- Thread-level performance tracking

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│ docker-compose.crawler.yml                              │
├─────────────────────────────────────────────────────────┤
│ imageboard_orchestrator  →  OTEL Metrics              │
│ imageboard_worker         →  OTEL Metrics              │
│ metrics_collector         →  Docker Stats + Pushgateway │
└─────────────────────────────────────────────────────────┘
                          ↓
                   pushgateway:9091
                          ↓
                   prometheus:9090
                          ↓
              JSON exports + Live Dashboard
```

## Quick Start

1. Start all services:
   ```bash
   ./start_otel_monitoring.sh
   ```

2. Start monitoring session (4 hours, conservative alerts):
   ```bash
   python monitor_imageboard_otel.py --duration 240 --alerts conservative
   ```

## Service Access

- **Prometheus**: http://localhost:9090
- **Pushgateway**: http://localhost:9091
- **Dashboard**: http://localhost:5001
- **Neo4j Browser**: http://localhost:7474

## Metrics Collected

### System Metrics
- Orchestrator/Worker CPU %
- Orchestrator/Worker Memory %
- Queue depth
- Container health status

### Orchestrator Metrics
- Catalog polls (total/success/failed)
- Threads discovered/queued
- Catalog fetch duration

### Worker Metrics
- Jobs processed (total/success/failed)
- Queue depth
- Job processing duration

### Thread-Level Metrics
- Posts collected per thread
- Images downloaded per thread
- Duplicate images found
- Moderated posts
- Fetch duration per thread

## Alert Thresholds (Conservative)

- **Service stopped**: Any container not running
- **Queue backlog**: Queue depth > 100 for > 10 minutes
- **High failure rate**: Job failure rate > 20% for > 5 minutes
- **No jobs processed**: No jobs for > 15 minutes

## Data Export

Metrics are exported to `logs/metrics/`:

- `metrics_YYYYMMDD_HHMMSS.json` - Snapshots every 5 minutes
- `report_monitor_YYYYMMDD_HHMMSS.md` - Final summary report

## Manual Commands

### Start services
```bash
docker compose -f docker-compose.crawler.yml up -d \
  imageboard_orchestrator \
  imageboard_worker \
  imageboard_dashboard \
  prometheus \
  pushgateway \
  metrics_collector
```

### Stop services
```bash
docker compose -f docker-compose.crawler.yml down
```

### View logs
```bash
# Orchestrator
docker logs -f imageboard_orchestrator

# Worker
docker logs -f imageboard_worker

# Prometheus
docker logs -f imageboard_prometheus
```

### Check metrics in Prometheus
```bash
# Query catalog polls
curl -s "http://localhost:9090/api/v1/query?query=imageboard_catalog_polls_total"

# Query jobs processed
curl -s "http://localhost:9090/api/v1/query?query=imageboard_jobs_processed_total"

# Query queue depth
curl -s "http://localhost:9090/api/v1/query?query=imageboard_queue_depth"
```

## Default Filter Configuration

The orchestrator uses these keywords to discover threads from `/b/` board:
```
["irl", "face", "celeb", "JJ", "girl", "girls", "feet", "cel", "panties", "gooning", "goon", "zoomers", "goddess", "built", "ecdw"]
```

To modify keywords, edit `IMAGEBOARD_KEYWORDS` environment variable in `docker-compose.crawler.yml`.

## Monitoring Dashboard

Live console display shows:
- Service status with CPU/memory
- Current metrics summary
- Active threads
- Recent alerts

Example:
```
┌─────────────────────────────────────────────────────────┐
│ IMAGEBOARD CRAWLER - OTEL MONITORING                   │
│ Duration: 45m | Check #90                            │
├─────────────────────────────────────────────────────────┤
│ STATUS: HEALTHY                                        │
│ ─────────────────────────────────────────────────────  │
│ Orchestrator: Running (CPU: 2.1%, MEM: 1.2%)          │
│ Worker: Running (CPU: 15.3%, MEM: 3.8%)               │
│                                                         │
│ METRICS SUMMARY (Current):                              │
│ ─────────────────────────────────────────────────────  │
│ Catalog polls: 12 | Jobs processed: 45                  │
│ Jobs success: 44 | Jobs failed: 1                        │
│ Queue depth: 12                                        │
│ Success rate: 97.8%                                    │
│                                                         │
│ ALERTS: NONE                                           │
└─────────────────────────────────────────────────────────┘
```

## Troubleshooting

### OTEL import errors
The crawler code gracefully handles missing OTEL dependencies. If you see "OTEL metrics: DISABLED", check that `requirements-otel.txt` was installed during container build.

### Prometheus not receiving metrics
1. Check pushgateway is running: `docker ps | grep pushgateway`
2. Check metrics_collector is running: `docker ps | grep metrics_collector`
3. View metrics_collector logs: `docker logs imageboard_metrics_collector`

### Queue building up
- Check worker is processing jobs: `docker logs imageboard_worker`
- Increase worker concurrency (modify `WORKER_CONCURRENCY` in environment)
- Check for errors: `docker logs imageboard_worker | grep ERROR`

### High CPU usage
- Check catalog poll interval (default 30min)
- Check thread monitoring interval (default 10min)
- Reduce concurrent monitors

## Next Steps

After 4-hour monitoring session:
1. Review `logs/metrics/report_*.md` for summary
2. Analyze individual `metrics_*.json` files
3. Query Prometheus web UI for trends: http://localhost:9090
4. Export data for further analysis (JSON format)
