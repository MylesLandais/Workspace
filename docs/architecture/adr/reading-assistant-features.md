# Reading Assistant Features

## Status

Accepted

## Context

Users need assistance while reading content:
- Quick summaries of long articles
- Answers to questions about the content
- Explanations of complex concepts
- Highlighting and annotation capabilities
- Text-to-speech for hands-free reading
- Reading progress tracking across devices
- AI-powered "ghost reader" that continues reading where you left off

These features require AI integration, real-time synchronization, and cross-platform support.

## Decision

Implement a comprehensive reading assistant system with:
1. **AI-powered summarization and Q&A** - Using LiteLLM with context-aware prompts
2. **Annotation system** - Highlighting, notes, and tags stored in Neo4j graph
3. **Text-to-speech** - Integration with browser/OS TTS APIs
4. **Reading progress tracking** - Real-time sync via Valkey, persistent storage in Neo4j
5. **Ghost reader** - AI continues reading and provides context when user returns

## Rationale

**User Experience**: Reading assistants significantly improve comprehension and engagement, especially for long-form content.

**Competitive Parity**: Features match or exceed capabilities of Readwise Reader and similar platforms.

**AI Integration**: Leverages existing AI agent architecture for consistent implementation.

**Graph Storage**: Annotations stored as graph relationships enable rich queries (e.g., "all my highlights about AI").

**Real-Time Sync**: Valkey enables instant progress sync across devices without Neo4j latency.

**Accessibility**: Text-to-speech improves accessibility and enables hands-free reading.

## Consequences

**Positive**:
- Significantly improved user experience
- Competitive feature parity
- Leverages existing AI infrastructure
- Graph storage enables rich annotation queries
- Real-time sync provides seamless cross-device experience
- Accessibility improvements

**Negative**:
- AI API costs for summarization and Q&A
- Text-to-speech quality varies by platform
- Progress sync adds complexity
- Annotation storage increases Neo4j usage
- Ghost reader requires maintaining reading context

**Neutral**:
- Requires tuning AI prompts for quality
- May need to cache TTS audio for performance
- Progress tracking needs conflict resolution for simultaneous edits

## Alternatives Considered

**No AI Features**: Would reduce costs but significantly impact user experience and competitive position.

**Third-Party TTS Services**: Services like Google Cloud TTS provide better quality but add cost and latency.

**Client-Side Only Progress**: Storing progress only in browser would be simpler but breaks cross-device sync.

**Separate Annotation Database**: Storing annotations separately would reduce Neo4j load but breaks graph queries.

## Implementation Notes

### AI Summarization

```python
async def generate_summary(item_id: str, user_id: str) -> str:
    # Check cache first
    cache_key = f"ai:summary:{item_id}:{user_id}"
    cached = await valkey.get(cache_key)
    if cached:
        return json.loads(cached)
    
    # Get item content
    item = await neo4j.get_item(item_id)
    
    # Get user's reading history for context
    user_context = await neo4j.get_user_reading_context(user_id)
    
    # Generate summary with context
    prompt = f"""Summarize this article in 3-5 bullet points, focusing on key insights.

User's recent reading topics: {user_context.topics}
User's interests: {user_context.interests}

Article:
{item.content}

Provide a concise summary that helps the user quickly understand the main points."""
    
    summary = await litellm.acompletion(
        model="openrouter/anthropic/claude-3-haiku",
        messages=[{"role": "user", "content": prompt}]
    )
    
    # Cache for 24 hours
    await valkey.setex(cache_key, 86400, json.dumps(summary))
    
    return summary
```

### Q&A About Content

```python
async def answer_question(item_id: str, question: str, user_id: str) -> str:
    # Get item content
    item = await neo4j.get_item(item_id)
    
    # Get related items from graph for context
    related = await neo4j.query("""
        MATCH (i:Item {id: $item_id})-[:TAGGED_WITH]->(t:Tag)
        MATCH (related:Item)-[:TAGGED_WITH]->(t)
        WHERE related.id <> $item_id
        RETURN related
        LIMIT 5
    """, item_id=item_id)
    
    # Build context from related items
    context = "\n\nRelated content:\n" + "\n".join([
        f"- {r.title}: {r.summary}" for r in related
    ])
    
    prompt = f"""Answer this question about the article:

Question: {question}

Article:
{item.content}
{context}

Provide a clear, concise answer. If the answer isn't in the article, say so and provide related information from the context."""
    
    answer = await litellm.acompletion(
        model="openrouter/anthropic/claude-3-haiku",
        messages=[{"role": "user", "content": prompt}]
    )
    
    # Store Q&A in graph for future reference
    await neo4j.create_qa(item_id, question, answer, user_id)
    
    return answer
```

### Annotation System

```cypher
// Annotation data model
(:User)-[:ANNOTATED {created_at: datetime, type: 'highlight'|'note'}]->(:Annotation {
  id: string,
  text: string,
  color: string,
  position: {start: int, end: int},
  note: string  // optional margin note
})

(:Annotation)-[:ON_ITEM]->(:Item)
(:Annotation)-[:TAGGED_WITH]->(:Tag)
```

```python
async def create_annotation(
    user_id: str,
    item_id: str,
    text: str,
    position: dict,
    color: str = "yellow",
    note: str = None
) -> str:
    annotation_id = generate_id()
    
    # Create annotation in Neo4j
    await neo4j.query("""
        MATCH (u:User {id: $user_id})
        MATCH (i:Item {id: $item_id})
        CREATE (a:Annotation {
            id: $annotation_id,
            text: $text,
            color: $color,
            position: $position,
            note: $note,
            created_at: datetime()
        })
        CREATE (u)-[:ANNOTATED]->(a)
        CREATE (a)-[:ON_ITEM]->(i)
        RETURN a.id
    """, 
        user_id=user_id,
        item_id=item_id,
        annotation_id=annotation_id,
        text=text,
        color=color,
        position=position,
        note=note
    )
    
    # Invalidate cache
    await valkey.delete(f"annotations:{user_id}:{item_id}")
    
    # Publish update event
    await valkey.publish(f"item:{item_id}:annotations", json.dumps({
        "type": "annotation_created",
        "annotation_id": annotation_id,
        "user_id": user_id
    }))
    
    return annotation_id
```

### Reading Progress Tracking

```python
async def update_reading_progress(
    user_id: str,
    item_id: str,
    position: int,  # character position or scroll percentage
    device_id: str = None
):
    # Update in Valkey for real-time sync
    progress_key = f"reading:{user_id}:{item_id}"
    await valkey.hset(progress_key, mapping={
        "position": position,
        "updated_at": datetime.now().isoformat(),
        "device_id": device_id or "unknown"
    })
    await valkey.expire(progress_key, 86400 * 7)  # 7 days
    
    # Periodically sync to Neo4j (every 30 seconds or on close)
    await queue_sync_to_neo4j(user_id, item_id, position)

async def sync_progress_to_neo4j(user_id: str, item_id: str, position: int):
    await neo4j.query("""
        MATCH (u:User {id: $user_id})
        MATCH (i:Item {id: $item_id})
        MERGE (u)-[r:READ]->(i)
        SET r.position = $position,
            r.last_read_at = datetime(),
            r.updated_at = datetime()
    """, user_id=user_id, item_id=item_id, position=position)
```

### Ghost Reader

```python
async def get_ghost_reader_context(user_id: str, item_id: str) -> dict:
    # Get reading progress
    progress = await neo4j.get_reading_progress(user_id, item_id)
    
    if not progress or progress.position < 100:  # Not finished
        # Get content from current position
        item = await neo4j.get_item(item_id)
        content_from_position = item.content[progress.position:]
        
        # Generate continuation context
        continuation = await litellm.acompletion(
            model="openrouter/google/gemini-flash-1.5",
            messages=[{
                "role": "user",
                "content": f"""You're helping a user continue reading. They've read up to this point:

{item.content[:progress.position]}

Provide a brief 2-3 sentence summary of what comes next to help them pick up where they left off. Don't spoil major points, just provide context."""
            }]
        )
        
        return {
            "position": progress.position,
            "continuation": continuation,
            "estimated_time_remaining": estimate_reading_time(
                len(item.content) - progress.position
            )
        }
    
    return None  # Already finished
```

### Text-to-Speech

```typescript
// Client-side TTS implementation
class TextToSpeech {
  private synth: SpeechSynthesis;
  private voices: SpeechSynthesisVoice[];
  
  constructor() {
    this.synth = window.speechSynthesis;
    this.loadVoices();
  }
  
  private loadVoices() {
    this.voices = this.synth.getVoices();
    // Prefer natural-sounding voices
    this.voices.sort((a, b) => {
      if (a.localService && !b.localService) return -1;
      if (!a.localService && b.localService) return 1;
      return 0;
    });
  }
  
  async speak(text: string, options: {
    rate?: number;
    pitch?: number;
    voice?: string;
  } = {}) {
    return new Promise<void>((resolve, reject) => {
      const utterance = new SpeechSynthesisUtterance(text);
      
      utterance.rate = options.rate || 1.0;
      utterance.pitch = options.pitch || 1.0;
      utterance.voice = options.voice 
        ? this.voices.find(v => v.name === options.voice) || null
        : this.voices[0];
      
      utterance.onend = () => resolve();
      utterance.onerror = (e) => reject(e);
      
      this.synth.speak(utterance);
    });
  }
  
  stop() {
    this.synth.cancel();
  }
  
  pause() {
    this.synth.pause();
  }
  
  resume() {
    this.synth.resume();
  }
}
```

### Annotation Queries

```cypher
// Get all user's highlights about a topic
MATCH (u:User {id: $user_id})-[:ANNOTATED]->(a:Annotation)
MATCH (a)-[:TAGGED_WITH]->(t:Tag {name: $topic})
RETURN a.text, a.note, a.created_at
ORDER BY a.created_at DESC

// Find items with most annotations (user's most engaged content)
MATCH (u:User {id: $user_id})-[:ANNOTATED]->(a:Annotation)
MATCH (a)-[:ON_ITEM]->(i:Item)
RETURN i, count(a) as annotation_count
ORDER BY annotation_count DESC
LIMIT 10

// Get annotations with related items
MATCH (u:User {id: $user_id})-[:ANNOTATED]->(a:Annotation)
MATCH (a)-[:ON_ITEM]->(i:Item)
MATCH (i)-[:TAGGED_WITH]->(t:Tag)
MATCH (related:Item)-[:TAGGED_WITH]->(t)
WHERE related.id <> i.id
RETURN a, i, collect(DISTINCT related)[0..3] as related_items
```

## References

- [ADR: AI Agent Architecture](./ai-agent-architecture.md)
- [ADR: Valkey Caching Layer](./valkey-caching-layer.md)
- [Web Speech API](https://developer.mozilla.org/en-US/docs/Web/API/Web_Speech_API)
- [Readwise Reader Features](https://readwise.io/read)





