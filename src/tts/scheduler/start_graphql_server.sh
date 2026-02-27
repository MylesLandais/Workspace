#!/bin/bash
# Start the Feed Monitor GraphQL Server

echo "=========================================="
echo "Starting Feed Monitor GraphQL Server"
echo "=========================================="
echo ""
echo "GraphQL endpoint: http://localhost:8001/graphql"
echo "WebSocket: ws://localhost:8001/graphql"
echo ""
echo "Press Ctrl+C to stop"
echo "=========================================="
echo ""

docker exec -w /home/jovyan/workspace jupyter python3 src/feed/graphql/server.py








