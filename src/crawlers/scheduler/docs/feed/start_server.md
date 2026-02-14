# How to Start the Feed Monitor Web Server

## Quick Start

```bash
# Start the server (you'll see output)
docker exec -w /home/jovyan/workspace jupyter python3 src/feed/web/server.py
```

The server will:
- Print startup messages
- Show the URL (http://localhost:8000)
- Display logs for each request

## To Run in Background

```bash
# Start in background and see output
docker exec -d -w /home/jovyan/workspace jupyter python3 src/feed/web/server.py

# Check if it's running
docker exec jupyter curl http://localhost:8000/api/stats

# View logs (if running in background)
docker logs jupyter | grep -i "feed\|uvicorn" | tail -20
```

## Test the Server

```bash
# Test if server is responding
docker exec -w /home/jovyan/workspace jupyter python3 test_feed_server.py
```

## Access the Interface

Once running, access:
- **Web Interface**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **API Stats**: http://localhost:8000/api/stats

## Troubleshooting

If the server doesn't start:
1. Check Neo4j connection: `docker exec jupyter python3 -c "from feed.storage.neo4j_connection import get_connection; get_connection()"`
2. Check if port 8000 is available
3. View error messages in the output

## Stop the Server

```bash
# Find the process
docker exec jupyter ps aux | grep server.py

# Kill it (replace PID)
docker exec jupyter kill <PID>
```







