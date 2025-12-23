# Reverse Image Search Integration

## Status

Accepted

## Context

Users encounter images in feeds without proper tags, metadata, or source information. They need to:
- Find the original source of an image ("find the sauce")
- Discover the artist or creator
- Enrich images with accurate tags from authoritative sources (Booru networks, Pixiv)
- Find higher-resolution versions
- Discover related content from the same series or artist

Traditional reverse image search (Google Images, TinEye) is insufficient for anime/art content. Specialized services like SauceNAO provide better results for this content type.

## Decision

Integrate SauceNAO reverse image search as a core feature for:
1. **Automatic tag enrichment** - Use RIS results to auto-tag images with character names, artists, resolutions
2. **Source discovery** - Link images back to original posts on Pixiv, Danbooru, etc.
3. **User-initiated search** - "Find Sauce" button on images for manual discovery
4. **Feed enhancement** - Automatically enrich feed images with source information
5. **Board curation** - Trace saved images to original sources for better organization

## Rationale

**Specialized for Art/Anime**: SauceNAO indexes major art/anime sources (Pixiv, Danbooru, Gelbooru, yande.re) with high accuracy, making it ideal for our Booru-style tagging system.

**Tag Enrichment**: RIS results include detailed tags, artist info, and character names that can be automatically imported into our Neo4j graph, creating richer relationships.

**Source Discovery**: Helps users find original sources, enabling subscription to creators and avoiding duplicates.

**NSFW-Friendly**: Strong support for mature content sources, aligning with our archival platform integrations (Kemono, Coomer).

**API Integration**: SauceNAO provides API access for automated enrichment workflows.

**User Value**: "Find the sauce" is a common user need in image-heavy communities, and providing this as a first-class feature differentiates our platform.

## Consequences

**Positive**:
- Significantly improves tag quality through automatic enrichment
- Enables source discovery and creator following
- Reduces duplicate content by linking to originals
- Enhances user experience with one-click source finding
- Creates richer graph relationships (Image → Tags → Artist → Related Works)
- Supports "goon-friendly" workflows for image discovery

**Negative**:
- API rate limits (free tier ~30 searches/day, paid for higher limits)
- Additional API costs for paid tier
- Requires handling API failures gracefully
- May need fallback services (IQDB for Booru-specific searches)
- Privacy considerations for user-uploaded images

**Neutral**:
- Requires API key management
- May need to cache results to manage rate limits
- Results quality varies by image type (works best for anime/art)

## Alternatives Considered

**Google Reverse Image Search**: General-purpose but poor results for anime/art content, no structured tag data.

**TinEye**: Good for finding duplicates but lacks source metadata and tag information.

**IQDB**: Booru-specific reverse image search, but limited to Booru networks only.

**Manual Tagging Only**: Users tag images themselves, but this is time-consuming and error-prone.

**No Reverse Search**: Simpler but misses significant value in tag enrichment and source discovery.

## Implementation Notes

### SauceNAO API Integration

```python
import saucenao
from saucenao import SauceNao

async def search_sauce(image_url: str, api_key: str) -> dict:
    """Search SauceNAO for image source."""
    # Check cache first
    cache_key = f"saucenao:{hashlib.md5(image_url.encode()).hexdigest()}"
    cached = await valkey.get(cache_key)
    if cached:
        return json.loads(cached)
    
    # Initialize SauceNAO client
    sauce = SauceNao(api_key=api_key)
    
    # Search by URL
    results = sauce.from_url(image_url)
    
    # Parse results
    parsed_results = []
    for result in results:
        parsed_results.append({
            "similarity": result.similarity,
            "thumbnail": result.thumbnail,
            "title": result.title,
            "author": result.author,
            "url": result.url,
            "source": result.source,
            "index_id": result.index_id,
            "index_name": result.index_name,
            "ext_urls": result.ext_urls
        })
    
    # Cache for 24 hours
    await valkey.setex(cache_key, 86400, json.dumps(parsed_results))
    
    return parsed_results
```

### Automatic Tag Enrichment Agent

```python
async def enrich_image_with_sauce(media_id: str, image_url: str):
    """Automatically enrich image with SauceNAO results."""
    # Search SauceNAO
    results = await search_sauce(image_url, SAUCENAO_API_KEY)
    
    if not results or results[0]["similarity"] < 80:  # Threshold
        return None
    
    best_match = results[0]
    
    # Extract tags from result
    # SauceNAO results link to Booru posts which have tags
    if "danbooru" in best_match["url"] or "gelbooru" in best_match["url"]:
        # Fetch tags from Booru post
        booru_tags = await fetch_booru_tags(best_match["url"])
        
        # Create tags in Neo4j
        await neo4j.create_tags_for_media(media_id, booru_tags)
    
    # Link to original source
    await neo4j.query("""
        MATCH (m:MediaItem {id: $media_id})
        MERGE (s:Source {url: $source_url})
        SET s.name = $source_name,
            s.type = $source_type
        CREATE (m)-[:ORIGINAL_POST]->(s)
    """, 
        media_id=media_id,
        source_url=best_match["url"],
        source_name=best_match["title"],
        source_type=best_match["source"]
    )
    
    # Link to artist if available
    if best_match.get("author"):
        await neo4j.query("""
            MATCH (m:MediaItem {id: $media_id})
            MERGE (a:Artist {name: $artist_name})
            CREATE (m)-[:CREATED_BY]->(a)
        """, media_id=media_id, artist_name=best_match["author"])
    
    return best_match
```

### User-Initiated "Find Sauce" Feature

```python
@app.post("/api/media/{media_id}/find-sauce")
async def find_sauce_for_image(media_id: str, user: User):
    """User-initiated reverse image search."""
    # Get media item
    media = await neo4j.get_media_item(media_id)
    
    # Check if already searched
    existing = await neo4j.query("""
        MATCH (m:MediaItem {id: $media_id})-[:ORIGINAL_POST]->(s:Source)
        RETURN s
    """, media_id=media_id)
    
    if existing:
        return {"status": "already_enriched", "source": existing[0]}
    
    # Search SauceNAO
    results = await search_sauce(media.url, SAUCENAO_API_KEY)
    
    if not results:
        return {"status": "no_results"}
    
    # Enrich with best match
    enrichment = await enrich_image_with_sauce(media_id, media.url)
    
    return {
        "status": "success",
        "results": results[:5],  # Top 5 results
        "enrichment": enrichment
    }
```

### Feed Enhancement Workflow

```python
async def enhance_feed_image(media_id: str):
    """Automatically enhance feed images with SauceNAO."""
    media = await neo4j.get_media_item(media_id)
    
    # Skip if already enriched
    if await neo4j.has_source_link(media_id):
        return
    
    # Only enrich if image has few/no tags (prioritize untagged content)
    tag_count = await neo4j.get_tag_count(media_id)
    if tag_count > 5:
        return  # Already well-tagged
    
    # Search SauceNAO
    results = await search_sauce(media.url, SAUCENAO_API_KEY)
    
    if results and results[0]["similarity"] >= 80:
        await enrich_image_with_sauce(media_id, media.url)
```

### Rate Limiting and Caching

```python
async def check_saucenao_rate_limit() -> bool:
    """Check if we can make a SauceNAO API call."""
    key = "ratelimit:saucenao:daily"
    count = await valkey.incr(key)
    
    if count == 1:
        await valkey.expire(key, 86400)  # 24 hour window
    
    # Free tier: 30 searches/day
    # Paid tier: higher limits
    daily_limit = SAUCENAO_DAILY_LIMIT  # From config
    
    if count > daily_limit:
        return False
    
    return True

async def cached_sauce_search(image_url: str) -> dict:
    """Search with caching and rate limiting."""
    # Check cache
    cache_key = f"saucenao:result:{hashlib.md5(image_url.encode()).hexdigest()}"
    cached = await valkey.get(cache_key)
    if cached:
        return json.loads(cached)
    
    # Check rate limit
    if not await check_saucenao_rate_limit():
        return {"error": "rate_limit_exceeded"}
    
    # Search
    results = await search_sauce(image_url, SAUCENAO_API_KEY)
    
    # Cache for 7 days (results don't change)
    await valkey.setex(cache_key, 604800, json.dumps(results))
    
    return results
```

### Integration with Tag System

```cypher
// After SauceNAO enrichment, create tag relationships
MATCH (m:MediaItem {id: $media_id})-[:ORIGINAL_POST]->(s:Source)
MATCH (s)-[:HAS_TAG]->(t:Tag)
MERGE (m)-[:HAS_TAG]->(t)

// Link to artist
MATCH (m:MediaItem {id: $media_id})-[:CREATED_BY]->(a:Artist)
MERGE (a)-[:CREATED]->(m)

// Find related works by same artist
MATCH (m:MediaItem {id: $media_id})-[:CREATED_BY]->(a:Artist)
MATCH (a)-[:CREATED]->(related:MediaItem)
WHERE related.id <> m.id
RETURN related
ORDER BY related.created_at DESC
LIMIT 20
```

### Fallback Services

```python
async def reverse_image_search_with_fallback(image_url: str) -> dict:
    """Try SauceNAO first, fallback to IQDB for Booru-specific searches."""
    # Try SauceNAO first
    saucenao_results = await cached_sauce_search(image_url)
    
    if saucenao_results and saucenao_results[0].get("similarity", 0) >= 80:
        return {"service": "saucenao", "results": saucenao_results}
    
    # Fallback to IQDB for Booru networks
    iqdb_results = await search_iqdb(image_url)
    
    if iqdb_results:
        return {"service": "iqdb", "results": iqdb_results}
    
    return {"service": "none", "results": []}
```

### Browser Extension Integration

```typescript
// Browser extension context menu integration
chrome.contextMenus.create({
  id: "find-sauce",
  title: "Find Sauce (SauceNAO)",
  contexts: ["image"]
});

chrome.contextMenus.onClicked.addListener(async (info, tab) => {
  if (info.menuItemId === "find-sauce") {
    // Send image URL to backend
    const response = await fetch(`${API_URL}/api/media/find-sauce`, {
      method: "POST",
      body: JSON.stringify({ image_url: info.srcUrl })
    });
    
    const results = await response.json();
    
    // Display results in popup or sidebar
    chrome.runtime.sendMessage({
      type: "saucenao_results",
      results: results
    });
  }
});
```

### Privacy and Ethical Considerations

- **User Consent**: Only search user-uploaded images with explicit consent
- **Rate Limiting**: Respect SauceNAO API limits, cache aggressively
- **Data Minimization**: Only store necessary metadata, not full images
- **Transparency**: Show users when images are auto-enriched
- **Opt-Out**: Allow users to disable automatic enrichment

## References

- [SauceNAO Official Site](https://saucenao.com/)
- [SauceNAO API Documentation](https://saucenao.com/user.php?page=search-api)
- [PySauceNAO Library](https://pypi.org/project/saucenao-api/)
- [ADR: Media Tagging and Visual Search](./media-tagging-visual-search.md)
- [ADR: AI Agent Architecture](./ai-agent-architecture.md)
- [IQDB Alternative](https://iqdb.org/)

