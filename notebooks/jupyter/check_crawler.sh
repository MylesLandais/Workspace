#!/bin/bash
# Check status of slow Reddit crawler

echo "=========================================="
echo "Slow Reddit Crawler Status"
echo "=========================================="
echo ""

# Check if process is running
if docker exec jupyter ps aux | grep "slow_reddit_crawler.py" | grep -v grep > /dev/null; then
    echo "Status: RUNNING"
    echo ""
    echo "Process details:"
    docker exec jupyter ps aux | grep slow_reddit_crawler | grep -v grep
    echo ""
    echo "Recent logs (last 20 lines):"
    docker logs jupyter --tail 20 2>&1 | tail -20
else
    echo "Status: NOT RUNNING"
    echo ""
    echo "To start the crawler:"
    echo "  docker exec -d -w /home/jovyan/workspace jupyter python3 slow_reddit_crawler.py"
fi

echo ""
echo "=========================================="
echo "To stop the crawler:"
echo "  docker exec jupyter pkill -f slow_reddit_crawler.py"
echo "=========================================="

