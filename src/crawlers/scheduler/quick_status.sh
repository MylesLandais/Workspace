#!/bin/bash
# Quick status check for the crawler

echo "=========================================="
echo "CRAWLER STATUS - $(date '+%Y-%m-%d %H:%M:%S')"
echo "=========================================="
echo ""

# Check if crawler is running
if docker exec jupyter ps aux | grep -q "slow_reddit_crawler.py" | grep -v grep; then
    echo "STATUS: RUNNING"
    echo ""
    docker exec jupyter ps aux | grep slow_reddit_crawler | grep -v grep
    echo ""
    
    # Get recent activity from logs
    echo "Recent Activity (last 20 lines):"
    docker logs jupyter --tail 100 2>&1 | grep -E "CYCLE|Processing r/|Collected|ERROR|DELAY" | tail -20
    echo ""
    
    # Check for issues
    LOGS=$(docker logs jupyter --tail 500 2>&1)
    if echo "$LOGS" | grep -qiE "429|rate.?limit"; then
        echo "!!! WARNING: Rate limit detected"
    fi
    if echo "$LOGS" | grep -qiE "403|forbidden|blocked"; then
        echo "!!! WARNING: Blocked/forbidden detected"
    fi
    if echo "$LOGS" | grep -qiE "captcha"; then
        echo "!!! WARNING: Captcha detected"
    fi
    
    if ! echo "$LOGS" | grep -qiE "429|403|captcha|rate.?limit|forbidden"; then
        echo "No bot detection signs - crawler appears healthy"
    fi
else
    echo "STATUS: NOT RUNNING"
    echo ""
    echo "To start:"
    echo "  docker exec -d -w /home/jovyan/workspace jupyter python3 slow_reddit_crawler.py"
fi

echo ""
echo "=========================================="








