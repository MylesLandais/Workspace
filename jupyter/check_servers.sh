#!/bin/bash
# Quick check of server status

echo "=== Server Status Check ==="
echo ""

echo "1. REST API (Port 8000):"
if docker exec jupyter curl -s http://localhost:8000/api/stats > /dev/null 2>&1; then
    echo "   ✓ Running"
    docker exec jupyter curl -s http://localhost:8000/api/stats | python3 -m json.tool 2>/dev/null || docker exec jupyter curl -s http://localhost:8000/api/stats
else
    echo "   ✗ Not running"
fi

echo ""
echo "2. GraphQL API (Port 8001):"
if docker exec jupyter curl -s http://localhost:8001/ > /dev/null 2>&1; then
    echo "   ✓ Running"
    docker exec jupyter curl -s http://localhost:8001/ | head -3
else
    echo "   ✗ Not running"
fi

echo ""
echo "3. Running Processes:"
docker exec jupyter ps aux | grep python3 | grep -E "server|graphql" | grep -v grep || echo "   No server processes found"

echo ""
echo "4. Port Status:"
docker exec jupyter ss -tlnp 2>/dev/null | grep -E "8000|8001" || docker exec jupyter netstat -tlnp 2>/dev/null | grep -E "8000|8001" || echo "   No servers listening on 8000 or 8001"








