# AI Agent Architecture

## Status

Accepted

## Context

The application needs AI capabilities for:
- Content summarization and explanation
- Q&A about documents
- Automatic tagging and categorization
- Content discovery and recommendations
- Reading assistance (ghost reader, highlighting suggestions)
- Feed health monitoring and content quality assessment

We need a flexible, cost-effective way to integrate multiple LLM providers while maintaining the ability to switch models based on task complexity and cost considerations.

## Decision

Use Google's Agent Development Kit (ADK) with LiteLLM as the backend abstraction layer, routing to multiple providers via OpenRouter API keys.

## Rationale

**Provider Flexibility**: LiteLLM provides a unified interface to multiple LLM providers (OpenAI, Anthropic, Google, etc.) via OpenRouter, allowing us to choose the best model for each task without vendor lock-in.

**Cost Optimization**: OpenRouter provides access to multiple models with different pricing tiers. We can route simple tasks (tagging, classification) to cheaper models (Gemini Flash) and complex tasks (summarization, Q&A) to more capable models (Claude Sonnet).

**Agent Framework**: Google ADK provides a structured framework for building agents with tools, context management, and conversation flows, which is essential for complex multi-step operations like content processing pipelines.

**Caching Integration**: LiteLLM supports Redis/Valkey caching, reducing API costs by caching similar queries and embeddings.

**Unified API**: Single interface for all AI operations simplifies codebase and makes it easier to swap providers or add new capabilities.

**OpenRouter Benefits**: Single API key management, automatic failover, usage analytics, and access to cutting-edge models as they're released.

## Consequences

**Positive**:
- Flexible model selection based on task complexity and cost
- Reduced vendor lock-in through abstraction layer
- Built-in caching reduces API costs
- Agent framework enables complex multi-step workflows
- Easy to add new AI capabilities without major refactoring
- OpenRouter provides usage analytics and cost tracking

**Negative**:
- Additional abstraction layer adds complexity
- Dependency on OpenRouter service availability
- Need to manage API key rotation and security
- Learning curve for Google ADK patterns
- Potential latency from routing through OpenRouter

**Neutral**:
- Requires monitoring of API costs and usage
- Need fallback strategies if OpenRouter is unavailable
- Model selection logic needs tuning for optimal cost/quality balance

## Alternatives Considered

**Direct Provider APIs**: Using OpenAI, Anthropic, etc. directly would provide better latency but lock us into specific vendors and require managing multiple API keys.

**Self-Hosted Models**: Running models locally (Ollama, vLLM) would eliminate API costs but requires significant infrastructure and may not match quality of commercial models.

**Single Provider**: Choosing one provider (e.g., OpenAI only) simplifies architecture but reduces flexibility and cost optimization opportunities.

**Custom Abstraction Layer**: Building our own abstraction would give full control but duplicates effort already solved by LiteLLM.

## Implementation Notes

### Model Selection Strategy

```python
# Intelligent model routing based on task complexity
def select_model(task_complexity: str, content_length: int) -> str:
    if task_complexity == "simple" and content_length < 500:
        # Fast, cheap model for simple tasks
        return "openrouter/google/gemini-flash-1.5"  # $0.075/1M tokens
    elif task_complexity == "medium":
        # Balanced model for moderate tasks
        return "openrouter/anthropic/claude-3-haiku"  # $0.25/1M tokens
    else:
        # High-quality model for complex tasks
        return "openrouter/anthropic/claude-3.5-sonnet"  # $3/1M tokens
```

### LiteLLM Configuration

```python
import litellm
from litellm import Cache

# Configure LiteLLM
litellm.set_verbose = True

# Enable caching via Valkey
litellm.cache = Cache(
    type="redis",
    host="valkey-host",
    port=6379,
    ttl=3600  # 1 hour cache
)

# Set default model
litellm.model = "openrouter/google/gemini-flash-1.5"

# Configure OpenRouter
os.environ["OPENROUTER_API_KEY"] = "your-key-here"
```

### Agent Design Patterns

**1. Content Processing Agents**

**Ingestion Agent**:
- Tools: Web scraper, RSS parser, HTML cleaner
- Flow: Fetch → Extract → Deduplicate → Enrich → Store
- Neo4j: Create Item nodes, link to Source, extract entities
- Valkey: Cache raw content, queue for processing

**Annotation Agent**:
- Tools: Highlight extraction, note summarization, tag suggestion
- Context: User's reading history from Neo4j, current item content from Valkey
- Output: Structured annotations stored in graph with relationships

**2. Discovery & Recommendation Agents**

**Topic Mapper Agent**:
- Input: New item content
- Tools: Entity extraction, topic modeling, graph traversal
- Neo4j Queries: Find related topics, similar items, citation networks
- LiteLLM: Use embedding models via OpenRouter to compute semantic similarity

**Feed Recommendation Agent**:
- Context: User's reading graph (Neo4j), engagement metrics (Valkey)
- Tools: Collaborative filtering, content-based filtering, graph algorithms
- Output: Ranked list of sources to explore

**3. Personalization Agents**

**Smart Inbox Agent**:
- Triggers: New items arrive, user opens app
- Logic:
  - Query Neo4j for user preferences, reading patterns
  - Fetch recent items from Valkey cache
  - Score items using LiteLLM (relevance prediction)
  - Update priority queue in Valkey

**Reading Assistant Agent**:
- Tools: Summarization, Q&A, definition lookup, citation finder
- Context Window: Current item + related items from Neo4j graph
- Caching: Store summaries in Valkey, embed citations in Neo4j

**4. Maintenance Agents**

**Feed Health Monitor**:
- Schedule: Hourly checks via Valkey sorted set
- Actions: Detect broken feeds, update frequency changes, content format shifts
- Neo4j: Update Source node properties, create health events

**Graph Pruning Agent**:
- Trigger: Near Aura free tier limits
- Logic: Archive old items, consolidate nodes, maintain important relationships
- Strategy: Keep high-value content (cited, annotated, referenced)

**5. Visual Analysis Agents**

**Image Tagging Agent**:
- Input: New media item (image)
- Tools: Vision model (CLIP, GPT-4V) for object detection, style recognition
- Context: Existing tags from source (Booru networks), user preferences
- Output: Suggested tags with confidence scores, stored in Neo4j with relationships
- LiteLLM: Use vision-capable models via OpenRouter (GPT-4V, Claude 3 Opus with vision)

**Visual Similarity Agent**:
- Input: Media item for similarity search
- Tools: Perceptual hashing, ML embeddings (CLIP)
- Context: Existing visual similarity index in Valkey
- Output: Ranked list of visually similar items
- Caching: Store embeddings in Valkey, cache similarity results

**Content Moderation Agent**:
- Input: Media item for content safety
- Tools: Vision model for NSFW detection, content classification
- Context: User preferences, platform policies
- Output: Content rating, safety flags, blur recommendations
- LiteLLM: Use fast models (Gemini Flash) for simple classification tasks

**SauceNAO Enrichment Agent**:
- Input: Media item without tags or with few tags
- Tools: SauceNAO API for reverse image search, Booru tag extraction
- Context: Existing tags (if any), user preferences
- Output: Enriched tags, source links, artist information
- Workflow: Search SauceNAO → Extract tags from results → Create tag relationships in Neo4j → Link to original source
- Caching: Cache SauceNAO results in Valkey to manage rate limits
- Trigger: Automatic for untagged images, manual via "Find Sauce" button

### Example Agent Workflow

**New Item Processing Pipeline**:

```python
async def process_new_item(item_id: str, source_id: str):
    # 1. Ingestion Agent fetches content → stores in Valkey
    raw_content = await ingestion_agent.fetch(item_id)
    await valkey.setex(f"feed:{source_id}:new:{item_id}", 3600, raw_content)
    
    # 2. Extraction Agent pulls from queue → parses → stores in Neo4j
    parsed = await extraction_agent.parse(raw_content)
    await neo4j.create_item(parsed)
    
    # 3. Topic Mapper Agent analyzes → creates Topic relationships
    topics = await topic_mapper_agent.analyze(parsed.content)
    await neo4j.create_topic_relationships(item_id, topics)
    
    # 4. Embedding Agent generates vectors → stores in Valkey
    embedding = await litellm.aembedding(
        model="openrouter/text-embedding-3-small",
        input=parsed.content
    )
    await valkey.hset(f"ai:embeddings:{item_id}", mapping={
        "model": "text-embedding-3-small",
        "vector": json.dumps(embedding)
    })
    
    # 5. Smart Inbox Agent recomputes priorities → updates user queues
    await smart_inbox_agent.update_priorities(item_id)
    
    # 6. Notification Agent checks user preferences → sends alerts
    await notification_agent.check_and_notify(item_id)
```

### Cost Optimization Strategies

**Batch Processing**:

```python
async def batch_embed(texts: list[str]):
    # Process 100 at a time to reduce API calls
    batches = [texts[i:i+100] for i in range(0, len(texts), 100)]
    embeddings = await asyncio.gather(*[
        litellm.aembedding(model="openrouter/text-embedding-3-small", input=batch)
        for batch in batches
    ])
    return embeddings
```

**Cache-First Strategy**:

```python
async def get_summary(item_id: str):
    # Check cache first
    cached = await valkey.get(f"ai:summary:{item_id}")
    if cached:
        return json.loads(cached)
    
    # Generate if not cached
    summary = await litellm.acompletion(
        model="openrouter/anthropic/claude-3-haiku",
        messages=[{
            "role": "user",
            "content": f"Summarize this content: {content}"
        }]
    )
    
    # Cache for 1 hour
    await valkey.setex(f"ai:summary:{item_id}", 3600, json.dumps(summary))
    return summary
```

### Visual Analysis Agent Examples

**Image Tagging Agent**:

```python
async def auto_tag_image(media_id: str, image_url: str) -> list[dict]:
    """Automatically tag image using vision model."""
    # Check cache
    cache_key = f"ai:tags:{media_id}"
    cached = await valkey.get(cache_key)
    if cached:
        return json.loads(cached)
    
    # Use vision model to analyze image
    tags = await litellm.acompletion(
        model="openrouter/openai/gpt-4-vision-preview",
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "Analyze this image and suggest tags in Booru format (character, artist, copyright, general, meta). Return JSON array of tags with categories."
                },
                {
                    "type": "image_url",
                    "image_url": {"url": image_url}
                }
            ]
        }]
    )
    
    # Parse and validate tags
    parsed_tags = parse_tag_response(tags)
    
    # Store in Neo4j with relationships
    await neo4j.create_tags_for_media(media_id, parsed_tags)
    
    # Cache for 24 hours
    await valkey.setex(cache_key, 86400, json.dumps(parsed_tags))
    
    return parsed_tags
```

**Visual Similarity Agent**:

```python
async def compute_visual_embedding(media_id: str, image_url: str) -> list[float]:
    """Compute visual embedding for similarity search."""
    # Check cache
    cache_key = f"media:embedding:{media_id}"
    cached = await valkey.hgetall(cache_key)
    if cached:
        return json.loads(cached["vector"])
    
    # Use CLIP model for visual embeddings
    embedding = await litellm.aembedding(
        model="openrouter/openai/clip-vit-base-patch32",
        input=image_url
    )
    
    # Store in Valkey
    await valkey.hset(cache_key, mapping={
        "vector": json.dumps(embedding),
        "model": "clip-vit-base-patch32"
    })
    await valkey.expire(cache_key, 604800)  # 7 days
    
    return embedding
```

**Content Moderation Agent**:

```python
async def moderate_content(media_id: str, image_url: str) -> dict:
    """Moderate content for safety and rating."""
    # Use fast model for simple classification
    moderation = await litellm.acompletion(
        model="openrouter/google/gemini-flash-1.5",
        messages=[{
            "role": "user",
            "content": f"Classify this image content: {image_url}. Return JSON with rating (safe/questionable/explicit) and requires_blur (boolean)."
        }]
    )
    
    result = json.loads(moderation)
    
    # Update media item in Neo4j
    await neo4j.update_media_rating(media_id, result["rating"])
    
    return result
```

### Error Handling and Fallbacks

```python
async def safe_ai_call(prompt: str, primary_model: str, fallback_model: str):
    try:
        return await litellm.acompletion(model=primary_model, messages=[...])
    except Exception as e:
        logger.warning(f"Primary model failed: {e}, falling back to {fallback_model}")
        return await litellm.acompletion(model=fallback_model, messages=[...])
```

### SauceNAO Enrichment Agent Example

```python
async def saucenao_enrichment_agent(media_id: str):
    """Enrich media item with SauceNAO reverse image search."""
    # Get media item
    media = await neo4j.get_media_item(media_id)
    
    # Check if already enriched
    if await neo4j.has_source_link(media_id):
        return {"status": "already_enriched"}
    
    # Check tag count - prioritize untagged content
    tag_count = await neo4j.get_tag_count(media_id)
    if tag_count > 5:
        return {"status": "sufficient_tags"}
    
    # Search SauceNAO
    results = await search_sauce(media.url, SAUCENAO_API_KEY)
    
    if not results or results[0]["similarity"] < 80:
        return {"status": "no_results"}
    
    best_match = results[0]
    
    # Extract tags from Booru source if available
    if "danbooru" in best_match["url"] or "gelbooru" in best_match["url"]:
        booru_tags = await fetch_booru_tags(best_match["url"])
        await neo4j.create_tags_for_media(media_id, booru_tags)
    
    # Link to original source
    await neo4j.create_source_link(media_id, best_match["url"], best_match["title"])
    
    # Link to artist
    if best_match.get("author"):
        await neo4j.create_artist_link(media_id, best_match["author"])
    
    return {"status": "enriched", "source": best_match}
```

## References

- [Google Agent Development Kit](https://ai.google.dev/adk)
- [LiteLLM Documentation](https://docs.litellm.ai/)
- [OpenRouter API](https://openrouter.ai/docs)
- [ADR: Valkey Caching Layer](./valkey-caching-layer.md)
- [ADR: Hybrid Search Architecture](./hybrid-search-architecture.md)
- [ADR: Media Tagging and Visual Search](./media-tagging-visual-search.md)
- [ADR: Reverse Image Search](./reverse-image-search.md)

- [Google Agent Development Kit](https://ai.google.dev/adk)
- [LiteLLM Documentation](https://docs.litellm.ai/)
- [OpenRouter API](https://openrouter.ai/docs)
- [ADR: Valkey Caching Layer](./valkey-caching-layer.md)
- [ADR: Hybrid Search Architecture](./hybrid-search-architecture.md)

