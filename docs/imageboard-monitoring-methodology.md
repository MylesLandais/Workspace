# Imageboard Monitoring - Methodology Review

## Current Approach Assessment

### What We're Doing
```
Every 5 minutes:
  1. Fetch full thread HTML (442KB per thread)
  2. Parse all posts
  3. Compare hash (simple post count)
  4. Overwrite HTML file (lose previous version)
  5. Update Neo4j with current state
  6. Download images
```

### Problems Identified

**1. No Version History**
- HTML files are overwritten
- Lost: Previous thread states
- Lost: Which posts were new in each crawl
- Lost: Conversation evolution over time

**2. Inefficient Polling**
- Downloads full 442KB HTML every 5 minutes
- Even when only 1 new post exists
- ~127GB of redundant data per thread per day

**3. Limited Change Detection**
- Only detects "new posts: 42"
- Don't know WHICH posts are new
- Don't know reply chains/relationships
- Missing context of conversation flow

**4. Missing Graph Relationships**
- Posts stored but not linked to replies
- Thread continuations detected but not visualized
- No timeline of thread evolution
- Hard to follow conversations

**5. Wasteful Image Downloads**
- Re-downloading same images on every crawl
- No deduplication logic
- Could be 90% redundant

## Alternative Methodologies

### Option 1: Event-Based Monitoring (Push vs Pull)

**Concept:**
- Use 4chan's WebSocket/API if available
- Receive push notifications for new posts
- Only fetch what changed

**Pros:**
- Real-time updates
- Minimal bandwidth usage
- No wasted polling

**Cons:**
- 4chan may not have public WebSocket
- More complex implementation
- May require reverse engineering

**Example:**
```python
class EventBasedMonitor:
    async def watch_thread(self, thread_id):
        ws = await connect_websocket(f"wss://4chan.org/ws/{thread_id}")
        async for event in ws:
            if event.type == "new_post":
                await store_incremental_post(event.data)
```

---

### Option 2: Incremental Fetching

**Concept:**
- Track last post number seen
- Only fetch new posts since last crawl
- Build thread state incrementally

**Pros:**
- 90% less data transfer
- Clear audit trail of what's new
- Easy to implement

**Cons:**
- Still polling-based
- Need to handle deleted posts
- More complex state management

**Example:**
```python
class IncrementalMonitor:
    def __init__(self):
        self.last_post_seen = {}  # {thread_id: last_post_no}

    def crawl_thread(self, thread_id):
        # Get last post number from database
        last_seen = self.last_post_seen.get(thread_id, 0)

        # Only fetch posts after last_seen
        new_posts = fetch_posts_since(thread_id, last_seen)

        # Store new posts with relationship to thread
        for post in new_posts:
            store_post_with_version(thread_id, post, timestamp=now())

        # Update last seen
        self.last_post_seen[thread_id] = new_posts[-1].post_no
```

**What this gives you:**
- Clear record: "Post 944340600 added at 18:20"
- Efficient: Only fetch new data
- Traceable: Full history of changes

---

### Option 3: Graph-First Relationship Tracking

**Concept:**
- Focus on relationships, not snapshots
- Track: Post → Reply, Thread → Continuation
- Version nodes for each crawl

**Neo4j Schema:**
```cypher
// Threads with version history
(t:Thread {board: "b", thread_id: 944340175})

// Thread versions (snapshots)
(tv:ThreadVersion {version: 1, crawled_at: "2026-01-02T18:00:00Z"})
(tv:ThreadVersion {version: 2, crawled_at: "2026-01-02T18:05:00Z"})

// Relationships
(t)-[:HAS_VERSION]->(tv)
(p:Post)-[:IN_THREAD_VERSION]->(tv)
(p1:Post)-[:REPLIES_TO]->(p2)

// Thread continuations
(t1:Thread)-[:CONTINUES_AS]->(t2:Thread)
```

**Pros:**
- Full conversation flow visible
- Track thread evolution
- Easy to query: "Show me all replies to post 944340500"
- Natural visualization

**Cons:**
- More complex queries
- More storage (version history)
- Need to handle deletions

---

### Option 4: Hybrid Approach (Recommended)

**Concept:**
- Poll catalog for new threads (efficient)
- Incremental fetch for active threads
- Archive snapshots at milestones

**Implementation:**
```python
class HybridMonitor:
    def __init__(self):
        self.catalog_poll_interval = 300  # 5 minutes
        self.thread_poll_interval = 60     # 1 minute (active threads)

    async def run(self):
        # 1. Poll catalog for new threads
        new_threads = await self.poll_catalog()
        for thread in new_threads:
            await self.start_monitoring(thread)

        # 2. Incremental fetch for active threads
        for thread_id in self.active_threads:
            await self.fetch_new_posts(thread_id)

        # 3. Archive snapshot at milestones
        if self.should_archive():
            await self.create_snapshot()

    async def fetch_new_posts(self, thread_id):
        last_seen = self.get_last_post(thread_id)

        # Fetch only new posts
        new_posts = await fetch_posts_since(thread_id, last_seen)

        # Store with relationships
        for post in new_posts:
            await self.store_post(thread_id, post)

        # Detect thread continuation
        if self.is_thread_ending(thread_id):
            continuation = self.find_continuation_thread(thread_id)
            await self.link_threads(thread_id, continuation)
```

**Milestones to archive:**
- Thread reaches 500 posts (bump limit)
- Thread pruned by moderation
- Thread is X hours old
- User manually requests archive

---

### Option 5: Versioned Filesystem + Graph

**Concept:**
- Keep all HTML versions on disk
- Use Git or similar for version control
- Graph for relationships and metadata

**File Structure:**
```
cache/imageboard/
├── threads/
│   └── b_944340175/
│       ├── versions/
│       │   ├── v001_2026-01-02_18-00.html (initial)
│       │   ├── v002_2026-01-02_18-05.html (+7 posts)
│       │   └── v003_2026-01-02_18-10.html (+42 posts)
│       └── current.html (symlink to latest)
├── images/
│   └── (organized by hash, not thread)
└── graph.db (Neo4j for relationships)
```

**Pros:**
- Full version history
- Easy to view timeline
- Git-style diffing
- Efficient storage (deduplication)

**Cons:**
- More complex file structure
- Need to manage versions
- Storage growth over time

---

## What Should We Do?

### Questions to Answer

1. **What's your primary goal?**
   - Archive threads for historical purposes?
   - Monitor for specific content in real-time?
   - Build a searchable database of content?
   - Analyze conversation patterns?

2. **How long do you need to keep data?**
   - 24 hours (temp monitoring)
   - 7 days (recent trends)
   - 30 days (monthly archive)
   - Indefinitely (historical record)

3. **What's more important?**
   - Speed of detection (real-time)
   - Storage efficiency
   - Query performance
   - Version history

4. **Do you need to visualize conversations?**
   - Reply chains (A → B → C)
   - Thread continuations (thread 1 → thread 2)
   - Timeline of thread evolution

### My Recommendation

**Hybrid Approach with Versioned Snapshots**

```python
# Core architecture
- Poll catalog every 5 minutes (efficient)
- Incremental fetch for active threads (every 1-2 minutes)
- Archive snapshots at milestones (post 100, 200, 300, etc.)
- Track relationships in Neo4j
- Keep version history on disk

# Storage
- Neo4j: Relationships, metadata, latest state
- Disk: Versioned HTML, images
- Graph: Reply chains, continuations, timeline

# Monitoring
- 5 min: Check catalog for new threads
- 1 min: Fetch new posts from active threads
- Event: Auto-follow thread continuations
```

**Benefits:**
- Efficient: Only fetch what changes
- Complete: Full version history
- Queryable: Easy to find specific posts/conversations
- Visualizable: Reply chains and evolution

---

## Next Steps

1. **Define requirements**: What do you actually need?
2. **Choose methodology**: Based on requirements
3. **Refactor monitor**: Implement new approach
4. **Test and iterate**: Verify it meets needs

Want me to implement a specific methodology?
