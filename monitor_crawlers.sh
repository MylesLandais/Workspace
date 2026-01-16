#!/bin/bash
# Monitor active Reddit RSS crawlers

echo "Reddit RSS Crawler Status"
echo "=================================="
echo ""

# Check running crawlers
echo "Active Processes:"
docker exec jupyter ps aux | grep crawl_reddit_rss | grep -v grep | while read line; do
    echo "  $line"
done

echo ""
echo "Database Status:"
docker exec -w /home/jovyan/workspace jupyter python3 -c "
import sys
sys.path.insert(0, 'src')
from feed.storage.neo4j_connection import get_connection
neo4j = get_connection()

# Get stats for each subreddit
subreddits = ['Sjokz', 'BrookeMonkTheSecond', 'BestOfBrookeMonk']
for subreddit in subreddits:
    result = neo4j.execute_read('''
        MATCH (p:Post)-[:POSTED_IN]->(s:Subreddit {name: \$subreddit})
        RETURN count(p) as total
    ''', parameters={'subreddit': subreddit})
    total = result[0]['total'] if result else 0
    
    result2 = neo4j.execute_read('''
        MATCH (p:Post)-[:POSTED_IN]->(s:Subreddit {name: \$subreddit})
        WHERE p.url CONTAINS \"i.redd.it\" OR p.url CONTAINS \"i.imgur.com\"
        RETURN count(p) as image_count
    ''', parameters={'subreddit': subreddit})
    image_count = result2[0]['image_count'] if result2 else 0
    
    print(f'  r/{subreddit}: {total} posts ({image_count} images)')
" 2>/dev/null || echo "  (Error querying database)"

echo ""
echo "To stop a crawler: docker exec jupyter pkill -f 'crawl_reddit_rss.py.*SubredditName'"








