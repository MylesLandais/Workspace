# RSS Inbox Checker & Creepy Crawly Spider

Check your RSS feeds for new posts and scrape full page content using the Creepy Crawly spider.

## Quick Start

### Option 1: Simple Check (for non-Cloudflare feeds)

```bash
# Check RSS feed
docker exec -w /home/jovyan/workspace jupyter python3 check_rss_simple.py

# Save new posts to database
docker exec -w /home/jovyan/workspace jupyter python3 check_rss_simple.py --save

# Only show posts after a specific date
docker exec -w /home/jovyan/workspace jupyter python3 check_rss_simple.py --since "2025-12-01 00:00:00"
```

### Option 2: Creepy Crawly Spider (for Cloudflare-protected feeds)

**For sites like femdom-pov.me that use Cloudflare protection:**

1. **Install Playwright first:**
   ```bash
   ./setup_playwright.sh
   ```
   This will install Playwright and the Chromium browser in your Docker container.

2. **Run the spider:**
   ```bash
   # Check RSS feed with full content scraping
   docker exec -w /home/jovyan/workspace jupyter python3 check_rss_inbox.py

   # Save new posts to database
   docker exec -w /home/jovyan/workspace jupyter python3 check_rss_inbox.py --save

   # Dry run (don't scrape full content, just list posts)
   docker exec -w /home/jovyan/workspace jupyter python3 check_rss_inbox.py --dry-run
   ```

## Features

### Simple RSS Checker (`check_rss_simple.py`)
- Fast, lightweight checking using `requests`
- Works with public RSS feeds
- Automatically detects Cloudflare protection and suggests using Playwright
- Filter posts by date
- Save to Neo4j database

### Creepy Crawly Spider (`check_rss_inbox.py`)
- 🕷️ Browser automation with Playwright
- Bypasses Cloudflare protection
- Scrapes full page content
- Extracts images from posts
- Extracts author and metadata
- Rate limiting for human-like behavior
- Saves complete data to Neo4j

## Usage Examples

### Check femdom-pov.me feed

```bash
# Quick check (will show Cloudflare error)
docker exec -w /home/jovyan/workspace jupyter python3 check_rss_simple.py --feed-url "https://femdom-pov.me/feed/"

# After installing Playwright - full check with content scraping
docker exec -w /home/jovyan/workspace jupyter python3 check_rss_inbox.py --feed-url "https://femdom-pov.me/feed/" --save
```

### Check multiple feeds

```bash
# Check different feed
docker exec -w /home/jovyan/workspace jupyter python3 check_rss_inbox.py --feed-url "https://example.com/feed/" --save
```

### Filter by date

```bash
# Only show posts after December 1, 2025
docker exec -w /home/jovyan/workspace jupyter python3 check_rss_inbox.py --since "2025-12-01 00:00:00" --save
```

### View in database

After saving posts, you can view them:

1. **Web Interface:**
   ```bash
   # Start the feed monitor web server
   ./start_feed_monitor.sh
   ```
   Then open http://localhost:8000

2. **GraphQL Query:**
   ```bash
   curl -X POST http://localhost:8000/graphql \
     -H "Content-Type: application/json" \
     -d '{"query": "{ posts(limit: 20) { title url created_utc } }"}'
   ```

3. **Direct Neo4j Query:**
   ```bash
   docker exec jupyter cypher-shell -u neo4j -p password \
     "MATCH (p:Post)-[:POSTED_IN]->(s:Subreddit {name: 'femdom-pov'}) RETURN p.title, p.url ORDER BY p.created_utc DESC LIMIT 10"
   ```

## How It Works

### Simple RSS Checker Flow

1. Fetch RSS feed using HTTP requests
2. Parse XML with feedparser
3. Extract post metadata (title, URL, date)
4. Filter by date if specified
5. Display new posts
6. Optionally save to database

### Creepy Crawly Spider Flow

1. **Browser Setup**: Launch Chromium with stealth settings
2. **Bypass Cloudflare**: Navigate through protection
3. **Fetch RSS**: Load feed XML via browser
4. **Parse Entries**: Extract post URLs
5. **Crawl Content**: Visit each post URL and scrape:
   - Full article text
   - All images
   - Author information
   - Published date
6. **Save to Database**: Store in Neo4j with rich metadata

## Troubleshooting

### "403 Forbidden" or "Cloudflare protection detected"

**Solution:** Use the Creepy Crawly spider instead:
```bash
./setup_playwright.sh
docker exec -w /home/jovyan/workspace jupyter python3 check_rss_inbox.py
```

### "Playwright not installed"

**Solution:** Run the setup script:
```bash
./setup_playwright.sh
```

### Database connection errors

**Solution:** Check that Neo4j is running and credentials are correct:
```bash
docker exec jupyter cypher-shell -u neo4j -p password "RETURN 1"
```

### No posts found

**Possible causes:**
- Feed URL is incorrect
- Site is down or blocking requests
- All posts are older than the --since date

**Try:**
- Remove --since flag to see all posts
- Use --dry-run to check if spider can access the feed
- Check the feed URL in a browser

## Command Line Options

### `check_rss_simple.py`

```
--feed-url    RSS feed URL to check (default: https://femdom-pov.me/feed/)
--since       Only show posts after this date (YYYY-MM-DD HH:MM:SS)
--save        Save new posts to database
```

### `check_rss_inbox.py`

```
--feed-url    RSS feed URL to check (default: https://femdom-pov.me/feed/)
--since       Only show posts after this date (YYYY-MM-DD HH:MM:SS)
--save        Save new posts to database
--dry-run     Don't scrape full content, just list posts
```

## Data Stored in Database

Each post stored in Neo4j includes:
- `title`: Post title
- `url`: Post URL
- `created_utc`: Publication date
- `selftext`: Full article content (scraped)
- `author`: Author name (if available)
- `score`, `num_comments`, `upvote_ratio`: Set to 0 for blog posts
- `over_18`: Set to false (can be enhanced)

Posts are connected to Subreddit nodes via `POSTED_IN` relationships.

## Next Steps

After checking your RSS inbox:

1. **View collected data** in the web interface
2. **Set up monitoring** to check regularly
3. **Export data** for analysis
4. **Integrate with other tools** in your feed monitoring system

## Notes

- The Creepy Crawly spider uses rate limiting (2-5 seconds delay) to avoid overwhelming servers
- All scraped content is stored in Neo4j for easy querying and analysis
- Images URLs are extracted and stored for further processing
- The system respects robots.txt when crawling (via the crawler_policy service)
