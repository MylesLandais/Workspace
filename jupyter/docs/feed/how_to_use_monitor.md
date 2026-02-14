# How to Use the Feed Monitor

## Start the Web Server

### Option 1: Using the startup script (recommended)
```bash
./start_feed_monitor.sh
```

This will:
- Show clear startup messages
- Display all server logs
- Show you exactly what's happening
- Let you see requests in real-time

### Option 2: Direct command
```bash
docker exec -w /home/jovyan/workspace jupyter python3 src/feed/web/server.py
```

## What You'll See

When you start the server, you'll see output like:
```
============================================================
Starting Feed Monitor Web Server
============================================================
Server will be available at: http://localhost:8000
API docs at: http://localhost:8000/docs
Press Ctrl+C to stop
============================================================
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

Then, as requests come in, you'll see:
```
INFO:     127.0.0.1:12345 - "GET /api/stats HTTP/1.1" 200 OK
INFO:     127.0.0.1:12345 - "GET / HTTP/1.1" 200 OK
```

## Access the Interface

Once running:
- **Web Dashboard**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs (interactive Swagger UI)
- **Statistics API**: http://localhost:8000/api/stats

## Test It's Working

In another terminal:
```bash
# Test the API
docker exec jupyter curl http://localhost:8000/api/stats

# Or use the test script
docker exec -w /home/jovyan/workspace jupyter python3 test_feed_server.py
```

## Stop the Server

Press `Ctrl+C` in the terminal where the server is running.

## Troubleshooting

**Server won't start?**
- Check Neo4j is accessible: `docker exec jupyter python3 -c "from feed.storage.neo4j_connection import get_connection; get_connection()"`
- Check port 8000 isn't already in use
- Look at the error messages in the output

**Can't access http://localhost:8000?**
- The server runs inside Docker, so you may need to:
  - Use the container's IP
  - Or set up port forwarding
  - Or access from within the container: `docker exec jupyter curl http://localhost:8000`

**Want to run in background?**
```bash
docker exec -d -w /home/jovyan/workspace jupyter python3 src/feed/web/server.py
# Then check logs with: docker logs jupyter | tail -20
```







