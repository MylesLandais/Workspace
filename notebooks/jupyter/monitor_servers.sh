#!/bin/bash
# Monitor feed server logs

echo "Monitoring Feed Servers..."
echo "Press Ctrl+C to stop"
echo ""

# Show recent logs
docker logs jupyter --tail 100 --follow 2>&1 | grep -E "server|graphql|uvicorn|FastAPI|INFO|ERROR|Started|Running|feed" --color=always








