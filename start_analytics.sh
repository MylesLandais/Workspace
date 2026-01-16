#!/bin/bash
# Start Analytics Dashboard

echo "=========================================="
echo "Imageboard Analytics Dashboard"
echo "=========================================="
echo ""

# Generate fresh analytics data
echo "1. Generating analytics data..."
docker compose exec jupyterlab python generate_analytics.py
echo ""

# Start analytics server
echo "2. Starting analytics server..."
docker compose exec -d jupyterlab python serve_analytics.py
echo ""

echo "=========================================="
echo "Dashboard is ready!"
echo "=========================================="
echo ""
echo "Access the dashboard at:"
echo "  http://localhost:8889"
echo ""
echo "Or use port forwarding from Docker:"
echo "  docker compose exec jupyterlab curl http://localhost:8889"
echo ""
echo "To stop the server:"
echo "  docker compose exec jupyterlab pkill -f serve_analytics.py"
echo ""
echo "To update analytics data:"
echo "  docker compose exec jupyterlab python generate_analytics.py"
echo ""
echo "=========================================="
