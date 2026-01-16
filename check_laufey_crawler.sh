#!/bin/bash
# Quick status check for laufeyhot crawler

echo "Laufeyhot Crawler Status"
echo "=================================="
echo ""

# Check if process is running
if docker exec jupyter ps aux | grep -q "crawl_laufey.py"; then
    echo "✓ Crawler is running"
    docker exec jupyter ps aux | grep "crawl_laufey.py" | grep -v grep
elif docker exec jupyter ps aux | grep -q "test_feed_subreddit.py laufeyhot"; then
    echo "✓ Crawler is running"
    docker exec jupyter ps aux | grep "test_feed_subreddit.py laufeyhot" | grep -v grep
elif docker exec jupyter ps aux | grep -q "crawl_reddit_json.py laufeyhot"; then
    echo "✓ Crawler is running"
    docker exec jupyter ps aux | grep "crawl_reddit_json.py laufeyhot" | grep -v grep
else
    echo "✗ Crawler is not running"
fi

echo ""
echo "Database Status:"
docker exec -w /home/jovyan/workspace jupyter python3 -c "
import sys
sys.path.insert(0, 'src')
from feed.storage.neo4j_connection import get_connection
neo4j = get_connection()

result = neo4j.execute_read('MATCH (p:Post)-[:POSTED_IN]->(s:Subreddit {name: \"laufeyhot\"}) RETURN count(p) as total')
total = result[0]['total'] if result else 0

img_result = neo4j.execute_read('''
    MATCH (p:Post)-[:POSTED_IN]->(s:Subreddit {name: \"laufeyhot\"})
    WHERE p.url CONTAINS \"i.redd.it\" OR p.url CONTAINS \"i.imgur.com\"
    RETURN count(p) as image_count
''')
img_count = img_result[0]['image_count'] if img_result else 0

print(f'  Posts collected: {total}')
print(f'  Image posts: {img_count}')
print(f'  Progress: {total}/300 ({(total/300*100):.1f}%)')
" 2>/dev/null || echo "  (Error querying database)"

echo ""
echo "To stop crawler: docker exec jupyter pkill -f 'crawl_laufey.py'"

