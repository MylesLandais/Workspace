# Entity Mapping for Facial Recognition

## Sunisa Lee Entity Tracking

### Source
- **Subreddit**: r/sunisalee
- **Entity**: Sunisa Lee
- **Target**: Track posts where entity "sunisa lee" appears
- **Context**: Olympic athlete, gymnastics, artistic swimming

### Current Status
- Post 1pw6w10 indexed with `entity_matched=sunisa lee`
- Title: "Sunisa Lee dressed up for The ESPYS 2025. IG Post July 2025."
- Score: 1045, 14 comments
- Images cached: 2 (139.4 KB total)
- Recent random sampling: 10 posts from last 30 days

### Implementation

**Database Schema**:
```cypher
MATCH (p:Post)
WHERE p.entity_matched = 'sunisa lee'
RETURN p
```

**Tags to Apply**:
- `p.entity_matched = 'sunisa lee'` - Entity name for tracking

### Future Development

1. **Facial Recognition Integration**
   - Extract images from posts tagged with sunisa lee
   - Run facial recognition to detect entity appearance
   - Create `(:Entity)-[:APPEARS_IN]->(:Post)` relationships

2. **Keyword Detection**
   - Pattern matching on post titles and selftext
   - Auto-tag posts with entity_matched field
   - Case-insensitive search: "sunisa lee", "sunisa"

3. **Entity Graph**
   - Create `(:Entity {name: 'Sunisa Lee'})` node
   - Link posts: `(:Entity)-[:MENTIONED_IN]->(:Post)`
   - Track appearance frequency over time

4. **Olympic Athlete Expansion**
   - Expand entity tracking to other Olympians
   - Related subreddits: r/gymnastics, r/swimming, r/artisticswimming
   - Multi-entity detection in single posts

### Monitoring Setup

**Subreddit Activity**:
- r/sunisalee: Sampled 10 posts (3 direct images, 1.24 MB)
- Note: Subreddit appears in monitoring lists but may have low recent activity

**Related Entities**:
- fasffy (r/TOS_girls, r/TOS_irls)
- sunisa lee (r/sunisalee)
- Future: Other Olympians, sports figures

### Notes
- Entity: Sunisa Lee is an Olympic athlete (gymnastics/artistic swimming)
- High-engagement posts: 1045 score, 14 comments on ESPYS 2025 post
- Source subreddits include both athletic and casual content
- Entity mapping enables cross-subreddit tracking

### Cross-Subreddit Detection
Target subreddits for sunisa lee appearances:
- r/gymnastics
- r/swimming
- r/artisticswimming
- r/Olympics
- r/lululemon (athletic clothing)
- r/Models (modeling content)

### Performance Metrics
- Direct image caching rate: ~30% of recent posts
- Gallery post processing: Full extraction (4+ images per gallery)
- Slow mode delays: 5-10s between requests
- Rate limit respectful: 100 posts per crawl with random delays
