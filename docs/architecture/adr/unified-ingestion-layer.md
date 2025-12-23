# Unified Ingestion Layer

## Status

Accepted

## Context

The application needs to ingest content from multiple sources:
- RSS feeds (traditional blogs, news sites)
- Custom web scraping (sites without RSS, social media)
- Email forwarding (newsletters, articles sent via email)
- Browser extension (save-anywhere functionality)
- API imports (third-party integrations)
- Social media platforms (Twitter, Instagram, TikTok, YouTube)
- **Reddit subreddits** (web scraping, no API access)
- **Booru networks** (e621, Danbooru, Gelbooru, Yande.re, Konachan) for image/media content
- **Archival platforms** (Kemono.su, Coomer.party) for paywalled content archives
- **Forum threads** (SimpCity.su) for thread-based content monitoring

Each source type has different:
- Update frequencies
- Content formats
- Authentication requirements
- Rate limiting constraints
- Error handling needs

We need a unified architecture that handles all these sources consistently while respecting their individual constraints.

## Decision

Implement a unified ingestion layer with:
1. **Source abstraction** - Common interface for all source types
2. **Queue-based processing** - Valkey queues for async ingestion
3. **Deduplication** - Bloom filters and content hashing
4. **Health monitoring** - Track feed health, update frequency, errors
5. **Rate limiting** - Per-source and per-domain rate limiting
6. **Content normalization** - Convert all sources to common Item format

## Rationale

**Consistency**: Single ingestion pipeline simplifies codebase and ensures consistent data quality across all sources.

**Scalability**: Queue-based architecture handles bursts and scales horizontally.

**Reliability**: Health monitoring and error handling prevent one broken source from affecting others.

**Efficiency**: Deduplication prevents storing the same content multiple times.

**Flexibility**: Easy to add new source types without major refactoring.

**Resource Management**: Rate limiting prevents overwhelming sources and getting blocked.

## Consequences

**Positive**:
- Consistent data model regardless of source
- Easy to add new source types
- Robust error handling and recovery
- Efficient deduplication across sources
- Health monitoring enables proactive issue detection
- Queue-based architecture scales well

**Negative**:
- More complex than single-source ingestion
- Need to handle many edge cases for different source types
- Scraping infrastructure requires maintenance (headless browsers, proxies)
- Rate limiting adds latency
- Health monitoring adds operational overhead

**Neutral**:
- Requires tuning for each source type
- May need third-party services for complex scraping (Browserless, Apify)
- Queue management requires monitoring

## Alternatives Considered

**Separate Pipelines**: One pipeline per source type would be simpler but duplicates logic and makes cross-source deduplication difficult.

**Synchronous Processing**: Processing sources synchronously would be simpler but doesn't scale and blocks on slow sources.

**Third-Party Aggregation**: Using services like Feedly API would simplify but adds cost and reduces control.

**Source-Specific Databases**: Storing each source type differently would optimize per-source but breaks unified queries and deduplication.

## Implementation Notes

### Source Abstraction

```typescript
interface Source {
  id: string;
  type: 'rss' | 'scrape' | 'email' | 'extension' | 'api' | 'social';
  config: SourceConfig;
  health: SourceHealth;
  lastSync: Date;
}

interface SourceConfig {
  url?: string;
  email?: string;
  apiKey?: string;
  selectors?: ScrapeSelectors;
  rateLimit?: RateLimitConfig;
  filters?: ContentFilters;
}

interface SourceHealth {
  status: 'healthy' | 'degraded' | 'broken';
  lastSuccess: Date;
  errorCount: number;
  avgUpdateFrequency: number;
  lastError?: string;
}
```

### Queue Architecture

```python
# Ingestion queue in Valkey
async def queue_ingestion_job(source_id: str, priority: int = 0):
    job = {
        "source_id": source_id,
        "type": "ingest",
        "priority": priority,
        "created_at": datetime.now().isoformat()
    }
    
    # Use sorted set for priority queue
    await valkey.zadd(
        "ingestion:queue",
        {json.dumps(job): priority}
    )

# Worker processes jobs
async def ingestion_worker():
    while True:
        # Get highest priority job
        jobs = await valkey.zrange("ingestion:queue", 0, 0, withscores=True)
        if not jobs:
            await asyncio.sleep(1)
            continue
        
        job_data = json.loads(jobs[0][0])
        source_id = job_data["source_id"]
        
        try:
            await ingest_source(source_id)
            await valkey.zrem("ingestion:queue", jobs[0][0])
        except Exception as e:
            logger.error(f"Ingestion failed for {source_id}: {e}")
            # Retry with backoff or move to dead letter queue
            await handle_ingestion_error(source_id, e)
```

### RSS Feed Ingestion

```python
import feedparser

async def ingest_rss(source: Source):
    feed = feedparser.parse(source.config.url)
    
    for entry in feed.entries:
        # Check deduplication
        url = entry.link
        if await is_duplicate(url):
            continue
        
        # Normalize to Item format
        item = {
            "title": entry.title,
            "url": url,
            "content": entry.summary or entry.content[0].value if entry.content else "",
            "published_at": entry.published_parsed,
            "source_id": source.id,
            "source_type": "rss"
        }
        
        # Queue for processing
        await queue_item_processing(item)
```

### Custom Web Scraping

```python
from playwright.async_api import async_playwright

async def ingest_scrape(source: Source):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        try:
            await page.goto(source.config.url)
            
            # Wait for content to load
            await page.wait_for_selector(source.config.selectors.content)
            
            # Extract content using selectors
            items = await page.evaluate(f"""
                () => {{
                    const elements = document.querySelectorAll('{source.config.selectors.item}');
                    return Array.from(elements).map(el => ({{
                        title: el.querySelector('{source.config.selectors.title}')?.textContent,
                        url: el.querySelector('{source.config.selectors.link}')?.href,
                        content: el.querySelector('{source.config.selectors.content}')?.textContent
                    }}));
                }}
            """)
            
            for item_data in items:
                if await is_duplicate(item_data["url"]):
                    continue
                
                item = normalize_item(item_data, source)
                await queue_item_processing(item)
                
        finally:
            await browser.close()
```

### Email Forwarding

```python
# Email ingestion via dedicated email address
async def ingest_email(email_data: dict):
    # Parse email
    subject = email_data["subject"]
    body = email_data["body"]
    from_email = email_data["from"]
    
    # Extract URL from email (common pattern)
    url = extract_url_from_email(body)
    
    if not url:
        # Treat entire email as content
        item = {
            "title": subject,
            "content": body,
            "source_id": f"email:{from_email}",
            "source_type": "email"
        }
    else:
        # Fetch and process URL
        item = await fetch_and_normalize_url(url)
        item["source_id"] = f"email:{from_email}"
        item["source_type"] = "email"
    
    await queue_item_processing(item)
```

### Browser Extension

```python
# API endpoint for browser extension
@app.post("/api/ingest/extension")
async def ingest_from_extension(data: dict, user: User):
    url = data["url"]
    title = data.get("title")
    selection = data.get("selection")  # User-selected text
    
    # Check deduplication
    if await is_duplicate(url):
        return {"status": "duplicate"}
    
    # Fetch full content
    content = await fetch_url_content(url)
    
    item = {
        "title": title or extract_title(content),
        "url": url,
        "content": content,
        "selected_text": selection,
        "source_id": f"extension:{user.id}",
        "source_type": "extension",
        "user_id": user.id
    }
    
    await queue_item_processing(item)
    return {"status": "queued", "item_id": item["id"]}
```

### Reddit Scraping

```python
# Reddit ingestion via web scraping (no API access)
# See ADR: Reddit Scraping Strategy for detailed implementation
async def ingest_reddit_subreddit(subreddit: str, source: Source):
    # Use old.reddit.com for simpler HTML parsing
    # Fallback to headless browser for new Reddit if needed
    posts = await scrape_old_reddit_subreddit(subreddit)
    
    for post in posts:
        # Check MD5 deduplication for media
        if post.get("media", {}).get("images"):
            for image_url in post["media"]["images"]:
                # Download and compute MD5
                md5_hash = await compute_image_md5(image_url)
                existing_id = await check_media_duplicate(md5_hash)
                
                if existing_id:
                    # Link to existing media item
                    await neo4j.create_cross_post_relationship(
                        source.id, 
                        existing_id,
                        {"reddit_post_id": post["id"]}
                    )
                    continue
                
                # Extract metadata
                metadata = await extract_image_metadata(image_url)
                
                item = {
                    "id": generate_id(),
                    "title": post["title"],
                    "url": post["url"],
                    "source_id": source.id,
                    "source_type": "reddit",
                    "media": {
                        "type": "image",
                        "url": image_url,
                        "width": metadata.get("width"),
                        "height": metadata.get("height"),
                        "format": metadata.get("format"),
                        "md5": md5_hash
                    },
                    "metadata": {
                        "reddit_post_id": post["id"],
                        "subreddit": subreddit,
                        "score": post["score"],
                        "author": post["author"],
                        "nsfw": post.get("nsfw", False),
                        "created_utc": post["created_utc"]
                    }
                }
                
                await queue_item_processing(item)
```

### Booru Network Ingestion

```python
# Booru network ingestion (e621, Danbooru, Gelbooru, Yande.re, Konachan)
async def ingest_booru_source(source: Source):
    # Booru APIs typically provide JSON endpoints
    api_url = f"{source.config.base_url}/posts.json"
    
    params = {
        "limit": 100,
        "page": await get_last_page(source.id)
    }
    
    # Add tag filters if configured
    if source.config.tags:
        params["tags"] = " ".join(source.config.tags)
    
    response = requests.get(api_url, params=params, headers={
        "User-Agent": source.config.user_agent
    })
    posts = response.json().get("posts", [])
    
    for post in posts:
        # Check MD5 deduplication
        md5_hash = post.get("md5")
        if md5_hash:
            existing_id = await check_media_duplicate(md5_hash)
            if existing_id:
                await neo4j.create_cross_post_relationship(
                    source.id,
                    existing_id,
                    {"booru_post_id": post["id"]}
                )
                continue
        
        # Extract tags and create tag relationships
        tags = post.get("tags", {})
        
        item = {
            "id": generate_id(),
            "title": post.get("tag_string", ""),
            "url": post.get("file_url") or post.get("source"),
            "source_id": source.id,
            "source_type": "booru",
            "media": {
                "type": "image",
                "url": post.get("file_url"),
                "width": post.get("width"),
                "height": post.get("height"),
                "file_size": post.get("file_size"),
                "format": post.get("file_ext"),
                "md5": md5_hash
            },
            "metadata": {
                "booru_post_id": post["id"],
                "score": post.get("score", 0),
                "favorites": post.get("fav_count", 0),
                "rating": post.get("rating"),  # safe, questionable, explicit
                "tags": {
                    "character": tags.get("character", []),
                    "artist": tags.get("artist", []),
                    "copyright": tags.get("copyright", []),
                    "general": tags.get("general", []),
                    "meta": tags.get("meta", [])
                }
            }
        }
        
        await queue_item_processing(item)
        
        # Process tags in background
        await queue_tag_processing(item["id"], tags)
```

### Archival Platform Ingestion (Kemono.su, Coomer.party)

```python
# Kemono.su and Coomer.party ingestion (archival sites for paywalled content)
async def ingest_archival_creator(source: Source):
    # Source config contains creator page URL
    # Example: https://kemono.su/patreon/user/12345
    creator_url = source.config.url
    
    # Poll creator page for new posts
    # These sites have no RSS, require periodic scraping
    response = requests.get(creator_url, headers={
        "User-Agent": source.config.user_agent
    })
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Extract posts from creator page
    posts = soup.select('article.post-card')
    
    for post_element in posts:
        post_id = post_element.get('id', '').replace('post-', '')
        post_url = f"{creator_url}/{post_id}"
        
        # Check if already ingested
        if await is_duplicate(post_url):
            continue
        
        # Extract post metadata
        title = post_element.select_one('.post-card__title')?.text or ""
        published = post_element.select_one('time')?.get('datetime', '')
        
        # Extract attachments (images, files)
        attachments = []
        for attachment in post_element.select('.post__attachment'):
            file_url = attachment.get('href', '')
            file_name = attachment.text.strip()
            attachments.append({
                "url": file_url,
                "name": file_name,
                "type": detect_file_type(file_url)
            })
        
        # Extract post content
        content = post_element.select_one('.post__content')?.text or ""
        
        item = {
            "id": generate_id(),
            "title": title,
            "url": post_url,
            "content": content,
            "source_id": source.id,
            "source_type": "archival",
            "metadata": {
                "archival_platform": source.config.platform,  # "kemono" or "coomer"
                "creator_id": extract_creator_id(creator_url),
                "platform": extract_platform(creator_url),  # "patreon", "fanbox", "onlyfans", etc.
                "post_id": post_id,
                "published_at": published,
                "attachments": attachments
            }
        }
        
        # Process attachments as separate media items
        for attachment in attachments:
            if attachment["type"] in ["image", "video"]:
                await queue_media_processing(item["id"], attachment)
        
        await queue_item_processing(item)
```

### Forum Thread Ingestion (SimpCity.su)

```python
# SimpCity.su thread monitoring (XenForo-based forum)
async def ingest_forum_thread(source: Source):
    # Source config contains thread URL
    # Example: https://simpcity.su/threads/creator-name.12345/
    thread_url = source.config.url
    
    # May require authentication cookies for watched threads
    cookies = source.config.cookies if source.config.cookies else {}
    
    response = requests.get(thread_url, headers={
        "User-Agent": source.config.user_agent
    }, cookies=cookies)
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Extract thread metadata
    thread_title = soup.select_one('h1.p-title')?.text or ""
    thread_id = extract_thread_id(thread_url)
    
    # Extract posts from thread
    posts = soup.select('article.message')
    
    for post_element in posts:
        post_id = post_element.get('data-content', '').split('-')[-1]
        post_url = f"{thread_url}#post-{post_id}"
        
        # Check if already ingested
        if await is_duplicate(post_url):
            continue
        
        # Extract post content
        content = post_element.select_one('.message-body')?.text or ""
        author = post_element.select_one('.username')?.text or ""
        posted_at = post_element.select_one('time')?.get('datetime', '')
        
        # Extract attachments (images, galleries)
        attachments = []
        for attachment in post_element.select('.attachment'):
            file_url = attachment.get('href', '')
            preview_url = attachment.select_one('img')?.get('src', '')
            attachments.append({
                "url": file_url,
                "preview_url": preview_url,
                "type": "image"
            })
        
        item = {
            "id": generate_id(),
            "title": f"{thread_title} - Post {post_id}",
            "url": post_url,
            "content": content,
            "source_id": source.id,
            "source_type": "forum",
            "metadata": {
                "forum_platform": "simpcity",
                "thread_id": thread_id,
                "thread_title": thread_title,
                "post_id": post_id,
                "author": author,
                "posted_at": posted_at,
                "attachments": attachments
            }
        }
        
        # Process attachments
        for attachment in attachments:
            await queue_media_processing(item["id"], attachment)
        
        await queue_item_processing(item)
```

### Media Metadata Extraction

```python
from PIL import Image
import exifread

async def extract_image_metadata(image_url: str) -> dict:
    """Extract metadata from image (dimensions, EXIF, format)."""
    # Download image
    response = requests.get(image_url)
    image_data = BytesIO(response.content)
    
    # Open with PIL
    img = Image.open(image_data)
    
    metadata = {
        "width": img.width,
        "height": img.height,
        "aspect_ratio": img.width / img.height,
        "format": img.format.lower(),
        "mode": img.mode
    }
    
    # Extract EXIF if available
    try:
        exif_data = img.getexif()
        if exif_data:
            metadata["exif"] = {
                "camera": exif_data.get(271),  # Make
                "model": exif_data.get(272),   # Model
                "date_taken": exif_data.get(306)  # DateTime
            }
    except:
        pass
    
    return metadata

async def compute_image_md5(image_url: str) -> str:
    """Compute MD5 hash of image for deduplication."""
    response = requests.get(image_url)
    return hashlib.md5(response.content).hexdigest()
```

### Deduplication

```python
import hashlib
from redis import BloomFilter

async def is_duplicate(url: str, content: str = None, md5_hash: str = None) -> bool:
    # Check URL in bloom filter
    if await valkey.bf_exists("seen:urls", url):
        return True
    
    # For media, check MD5 hash (most reliable)
    if md5_hash:
        if await valkey.bf_exists("seen:md5", md5_hash):
            return True
    
    # If content provided, check content hash
    if content:
        content_hash = hashlib.sha256(content.encode()).hexdigest()
        if await valkey.exists(f"content:hash:{content_hash}"):
            return True
    
    return False

async def mark_as_seen(url: str, content: str = None):
    # Add to bloom filter
    await valkey.bf_add("seen:urls", url)
    
    # Store content hash if provided
    if content:
        content_hash = hashlib.sha256(content.encode()).hexdigest()
        await valkey.setex(f"content:hash:{content_hash}", 86400 * 30, "1")  # 30 days
```

### Rate Limiting

```python
async def check_rate_limit(domain: str, source_id: str) -> bool:
    # Per-domain rate limiting
    domain_key = f"ratelimit:domain:{domain}"
    domain_count = await valkey.incr(domain_key)
    if domain_count == 1:
        await valkey.expire(domain_key, 60)  # 1 minute window
    
    if domain_count > 10:  # 10 requests per minute per domain
        return False
    
    # Per-source rate limiting
    source_key = f"ratelimit:source:{source_id}"
    source_count = await valkey.incr(source_key)
    if source_count == 1:
        await valkey.expire(source_key, 3600)  # 1 hour window
    
    if source_count > 100:  # 100 requests per hour per source
        return False
    
    return True
```

### Health Monitoring

```python
async def update_source_health(source_id: str, success: bool, error: str = None):
    health_key = f"source:health:{source_id}"
    
    if success:
        await valkey.hset(health_key, mapping={
            "last_success": datetime.now().isoformat(),
            "status": "healthy"
        })
        # Reset error count on success
        await valkey.hset(health_key, "error_count", 0)
    else:
        error_count = await valkey.hincrby(health_key, "error_count", 1)
        await valkey.hset(health_key, mapping={
            "last_error": error,
            "last_error_at": datetime.now().isoformat(),
            "status": "broken" if error_count > 5 else "degraded"
        })
    
    # Update in Neo4j
    await neo4j.update_source_health(source_id, success, error)

async def monitor_source_health():
    """Periodic health check for all sources"""
    sources = await neo4j.get_all_sources()
    
    for source in sources:
        # Check if source has updated recently
        last_success = await valkey.hget(f"source:health:{source.id}", "last_success")
        if last_success:
            last_success_dt = datetime.fromisoformat(last_success)
            hours_since_success = (datetime.now() - last_success_dt).total_seconds() / 3600
            
            # Alert if source hasn't updated in expected timeframe
            expected_frequency = source.config.expected_update_frequency_hours
            if hours_since_success > expected_frequency * 2:
                await alert_source_degraded(source.id, hours_since_success)
```

### Content Normalization

```python
def normalize_item(raw_item: dict, source: Source) -> dict:
    """Convert any source format to common Item format"""
    return {
        "id": generate_item_id(raw_item),
        "title": extract_title(raw_item),
        "url": extract_url(raw_item),
        "content": clean_content(extract_content(raw_item)),
        "published_at": parse_date(raw_item.get("published_at")),
        "source_id": source.id,
        "source_type": source.type,
        "metadata": {
            "author": extract_author(raw_item),
            "tags": extract_tags(raw_item),
            "images": extract_images(raw_item),
            "original_format": source.type
        }
    }
```

## References

- [ADR: Valkey Caching Layer](./valkey-caching-layer.md)
- [ADR: Neo4j Aura Optimization](./neo4j-aura-optimization.md)
- [ADR: Reddit Scraping Strategy](./reddit-scraping-strategy.md)
- [ADR: Media Tagging and Visual Search](./media-tagging-visual-search.md)
- [Feedparser Documentation](https://feedparser.readthedocs.io/)
- [Playwright Documentation](https://playwright.dev/python/)
- [Kemono.su](https://kemono.su/)
- [Coomer.party](https://coomer.party/)
- [SimpCity.su](https://simpcity.su/)

