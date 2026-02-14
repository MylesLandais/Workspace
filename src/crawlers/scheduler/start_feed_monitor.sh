#!/bin/bash
# Start the Feed Monitor Web Server with visible output

echo "=========================================="
echo "Starting Feed Monitor Web Server"
echo "=========================================="
echo ""
echo "The server will start and show logs below."
echo "Press Ctrl+C to stop the server."
echo ""
echo "Once started, access:"
echo "  - Web Interface: http://localhost:8000"
echo "  - API Docs: http://localhost:8000/docs"
echo "  - API Stats: http://localhost:8000/api/stats"
echo ""
echo "=========================================="
echo ""

docker exec -w /home/jovyan/workspace jupyter python3 src/feed/web/server.py








