# RSS Inbox Crawler Status Report

## Summary

Your RSS inbox checking system has been set up, but there are limitations due to Cloudflare protection on the target site.

## What We Set Up

### Files Created
1. **check_rss_simple.py** - Simple RSS checker using requests
2. **check_rss_enhanced.py** - Enhanced checker with better headers
3. **check_rss_inbox.py** - Creepy Crawly spider with Playwright (requires browser dependencies)
4. **setup_playwright.sh** - Script to install Playwright browser automation
5. **RSS_INBOX_README.md** - Complete documentation

### Database Schema
- ✅ Neo4j database schema created and ready
- ✅ BlogAdapter platform configured
- ✅ Ready to store posts from RSS feeds

## Current Status for femdom-pov.me

### Issue: Cloudflare Protection
The site https://femdom-pov.me/feed/ is protected by Cloudflare Turnstile, which blocks:
- Direct HTTP requests (403 Forbidden)
- Requests with enhanced headers
- Basic Playwright automation (missing system libraries)

### Current Database Status
- **Subreddits in database**: 0
- **Posts in database**: 0
- **Database schema**: Ready and migrated

## Available Options

### Option 1: Mock Mode (Testing Only)
Use BlogAdapter's mock mode to test the system:

```bash
docker exec -w /home/jovyan/workspace jupyter python3 check_rss_enhanced.py --mock
```

This returns a mock post showing the system works:
- Title: "Princess Lexie Height Comparison JOI"
- URL: https://femdom-pov.me/princess-lexie-height-comparison-joi/
- Date: 2025-12-20

### Option 2: Install System Libraries (Full Solution)
To run Creepy Crawly spider, you need to install missing system libraries. In your Docker container, run:

```bash
# These need to be installed with root access
apt-get update
apt-get install -y libnspr4 libnss3 libatk1.0-0 libatk-bridge2.0-0 \
  libcups2 libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 libxfixes3 \
  libxrandr2 libgbm1 libasound2 libpango-1.0-0 libcairo2 libatspi2.0-0
```

Then run the spider:
```bash
docker exec -w /home/jovyan/workspace jupyter python3 check_rss_inbox.py --save
```

### Option 3: Alternative Approach
If you can't install system libraries, consider:
- Using a proxy service that handles Cloudflare
- Setting up a separate VM/container with full browser dependencies
- Using a commercial RSS-to-API service
- Manually adding posts to database

### Option 4: Manual Ingestion
You can manually check the feed and add posts:

1. Visit https://femdom-pov.me/feed/ in your browser
2. Copy post URLs you want to ingest
3. Use the BlogAdapter to fetch and store them:

```python
from src.feed.platforms.blog import BlogAdapter
from src.feed.storage.neo4j_connection import get_connection

adapter = BlogAdapter()
neo4j = get_connection()

# Fetch specific post
posts, _ = adapter.fetch_posts(
    source='https://femdom-pov.me/feed/',
    limit=1
)

# Store manually
for post in posts:
    neo4j.execute_write("""
        MERGE (p:Post {url: $url})
        SET p.title = $title, p.selftext = $content,
            p.created_utc = $created_utc
        MERGE (s:Subreddit {name: 'femdom-pov'})
        MERGE (p)-[:POSTED_IN]->(s)
    """, parameters={
        'url': post.url,
        'title': post.title,
        'content': post.selftext,
        'created_utc': post.created_utc,
    })
```

## What the Spider Will Do (When Working)

When Creepy Crawly spider runs successfully with browser automation, it will:

1. **Launch Chromium browser** to bypass Cloudflare
2. **Navigate to feed URL** using browser context
3. **Parse RSS XML** to find all post entries
4. **Crawl each post** to extract:
   - Full article content (not just RSS excerpt)
   - All images from the post
   - Author information
   - Published date
   - Any metadata
5. **Save to Neo4j** with proper relationships
6. **Display summary** showing:
   - Total posts in feed
   - Number of new posts (since last check)
   - Details of each new post

## How Many New Posts

To check "how many new posts I haven't checked", you would:

1. **First run:** Check the feed and save all posts to database
2. **Subsequent runs:** Use `--since` parameter with the last check date

Example:
```bash
# Initial check - save all posts
docker exec -w /home/jovyan/workspace jupyter python3 check_rss_inbox.py --save

# Later - only check for posts since December 1, 2025
docker exec -w /home/jovyan/workspace jupyter python3 check_rss_inbox.py \
  --since "2025-12-01 00:00:00" --save
```

The system will then report:
- Total posts in feed
- How many are new (since your last check)
- Save only the new ones

## Viewing Results

After ingesting posts:

### Web Interface
```bash
./start_feed_monitor.sh
```
Then open: http://localhost:8000

### Direct Database Query
```bash
docker exec -w /home/jovyan/workspace jupyter python3 -c "
from src.feed.storage.neo4j_connection import get_connection

neo4j = get_connection()
result = neo4j.execute_read('''
MATCH (p:Post)-[:POSTED_IN]->(s:Subreddit {name: 'femdom-pov'})
RETURN p.title, p.url, p.created_utc
ORDER BY p.created_utc DESC
''')

for record in result:
    print(f'{record[\"p.title\"]} - {record[\"p.created_utc\"]}')
"
```

### GraphQL Query
```bash
curl -X POST http://localhost:8000/graphql \
  -H "Content-Type: application/json" \
  -d '{
    "query": "query { posts(filter: {subreddit: \"femdom-pov\"}) { title url created_utc } }"
  }'
```

## Current Limitations

1. **No browser automation**: Missing system libraries prevent Playwright from running
2. **Cloudflare protection**: Blocks all direct HTTP requests
3. **No proxy setup**: Would need external service to bypass Cloudflare
4. **Manual intervention required**: Currently need to manually ingest posts

## Recommendation

**To fully automate this RSS feed checking, you have two paths:**

### Path A: Fix Browser Automation (Recommended)
Install the required system libraries in your Docker container to enable Playwright. This gives you:
- ✅ Full automation
- ✅ Complete content scraping
- ✅ Regular monitoring capability
- ✅ No manual intervention

### Path B: Workaround (Quick Solution)
Manually add posts for now using the code snippet in Option 4 above. This gives you:
- ✅ Data in database
- ✅ Can use web interface
- ✅ No system changes needed
- ❌ Requires manual effort

## Next Steps

Choose your path:

**For Path A (Full Automation):**
1. Get root access to your Docker container
2. Install the system libraries listed in Option 2
3. Run: `docker exec -w /home/jovyan/workspace jupyter python3 check_rss_inbox.py --save`

**For Path B (Manual Solution):**
1. Visit https://femdom-pov.me/feed/ in your browser
2. Use the code snippet in Option 4 to add posts
3. View results via web interface: `./start_feed_monitor.sh`

## Help

For questions or issues, see:
- RSS_INBOX_README.md - Complete documentation
- README_FEED_MONITOR.md - Feed monitoring guide
- QUICKSTART_FEED_MONITOR.md - Quick start guide

---

**Status**: System ready, awaiting browser automation or manual data entry
**Database**: Empty, schema created
**Next Action**: Choose Path A or Path B above
