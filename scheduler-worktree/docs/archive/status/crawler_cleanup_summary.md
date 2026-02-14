# Crawler System Cleanup Summary

## Overview
Cleaned up and refactored the crawler (spidr) system to match updated ADR documentation. All Reddit crawling now consistently uses JSON API instead of HTML scraping.

## Changes Made

### 1. Documentation Updates
- **`crawl_reddit_rss.py`**: Updated docstring to clarify RSS is an alternative method, not the primary approach
- **`crawl_reddit_json.py`**: Updated docstring to emphasize it's the primary production method per ADR
- **`notebooks/media_processing/reddit_image_pipeline.ipynb`**: Added disclaimer that it's for ad-hoc processing only, not production
- **`src/image_crawler/README.md`**: Clarified BeautifulSoup is for general web pages, not Reddit

### 2. Code Cleanup
- **`crawl_reddit_subreddit.py`**: Removed unused BeautifulSoup import, added comment clarifying JSON API usage
- **`src/image_crawler/orchestrator.py`**: Added comment clarifying HTML parsing is for general web pages, not Reddit

### 3. Consistency Checks
All production Reddit crawling now uses:
- `RedditAdapter` from `src/feed/platforms/reddit.py` (JSON API)
- No HTML scraping for Reddit posts
- Clear separation: HTML parsing only for bio pages and general web pages

## Architecture Alignment

### Production Methods (JSON API)
- `src/feed/platforms/reddit.py` - Core RedditAdapter using JSON API
- `slow_reddit_crawler.py` - Production crawler
- `crawl_reddit_json.py` - Image-focused crawler
- `crawl_reddit_subreddit.py` - History tracking crawler

### Alternative Methods
- `crawl_reddit_rss.py` - RSS feed method (valid alternative, less metadata)

### Ad-hoc Tools
- `notebooks/media_processing/reddit_image_pipeline.ipynb` - One-off HTML scraping for specific URLs

### Other Uses of HTML Parsing (Valid)
- `src/feed/services/bio_crawler.py` - Parsing bio pages (not Reddit posts)
- `src/image_crawler/orchestrator.py` - General web page image extraction

## Verification

All crawler code now:
- ✅ Uses JSON API for Reddit posts (per ADR)
- ✅ Has clear documentation about method used
- ✅ Separates Reddit crawling from general HTML parsing
- ✅ Matches updated ADR documentation

## References
- ADR: `docs/architecture/adr/reddit-scraping-strategy.md`
- Implementation: `src/feed/platforms/reddit.py`






