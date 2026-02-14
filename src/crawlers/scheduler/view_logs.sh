#!/bin/bash
# View logs for both services

echo "=== Feed Monitor Service Logs ==="
echo "Press Ctrl+C to stop"
echo ""

# Show GraphQL logs
echo "--- GraphQL Server (8001) ---"
docker exec jupyter tail -f /tmp/graphql.log 2>/dev/null &
GRAPHQL_PID=$!

# Show REST API logs from docker logs
echo "--- REST API Server (8000) ---"
docker logs jupyter --follow 2>&1 | grep -E "server|8000|uvicorn|INFO|ERROR" &
REST_PID=$!

# Wait for both
wait $GRAPHQL_PID $REST_PID








