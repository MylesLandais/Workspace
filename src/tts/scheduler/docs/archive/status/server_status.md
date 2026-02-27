# Server Status & Startup Guide

## Current Status

**❌ No servers are currently running**

## Available Servers

### 1. GraphQL Server (Port 8001)
- **Purpose**: GraphQL API with subscriptions
- **Status**: Not running
- **Start**: `./start_graphql_server.sh` or see below

### 2. REST API Server (Port 8000)
- **Purpose**: FastAPI REST interface
- **Status**: Not running
- **Start**: `./start_feed_monitor.sh` or see below

## How to Start

### Start GraphQL Server

```bash
# Option 1: Use the script
./start_graphql_server.sh

# Option 2: Direct command
docker exec -w /home/jovyan/workspace jupyter python3 src/feed/graphql/server.py
```

**Access:**
- GraphQL: http://localhost:8001/graphql
- WebSocket: ws://localhost:8001/graphql

### Start REST API Server

```bash
# Option 1: Use the script
./start_feed_monitor.sh

# Option 2: Direct command
docker exec -w /home/jovyan/workspace jupyter python3 src/feed/web/server.py
```

**Access:**
- Web UI: http://localhost:8000
- API: http://localhost:8000/api/stats

## Check if Running

```bash
# Check GraphQL server
docker exec jupyter curl -s http://localhost:8001/graphql -X POST \
  -H "Content-Type: application/json" \
  -d '{"query": "{ stats { total_posts } }"}'

# Check REST API
docker exec jupyter curl -s http://localhost:8000/api/stats

# Check ports
docker exec jupyter ss -tlnp | grep -E "8000|8001"
```

## Run in Background

```bash
# GraphQL server in background
docker exec -d -w /home/jovyan/workspace jupyter python3 src/feed/graphql/server.py

# REST API in background
docker exec -d -w /home/jovyan/workspace jupyter python3 src/feed/web/server.py
```

## Stop Servers

```bash
# Find processes
docker exec jupyter ps aux | grep -E "server.py|graphql"

# Kill by PID (replace <PID>)
docker exec jupyter kill <PID>
```







