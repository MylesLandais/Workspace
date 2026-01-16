# Entity Mapping for Facial Recognition

## TOS Girls Entity Tracking

### Source
- **Subreddit**: r/TOS_girls (Note: Official subreddit name, also see r/TOS_girls, r/TOS_girls)
- **Entities**: Tannar, Loserfruit, Fasffy, Develique, Oasis, Nalopia, Aliythia, Berticuss
- **Target**: Track posts where these entity names appear
- **Context**: "Girls" - female creators, models, influencers from Total War Strategy (TOS) fandom

### Current Status
- 30 posts indexed with entity_matched tags
- Images cached: 11 (1.27 MB)
- Posts from r/TOS_girls: 100 total, 92 matching entities

### Entity List

| Entity | Posts | Notes |
|---------|--------|--------|
| Fasffy | Multiple | Already tracked separately |
| Tannar | 1+ | Official TOS girls member |
| Loserfruit | Multiple | Popular creator |
| Develique | Multiple | Content creator |
| Oasis | Multiple | Model/influencer |
| Nalopia | 1+ | Entity from fandom |
| Aliythia | 1+ | Entity from fandom |
| Berticuss | Multiple | Content creator |

### Implementation

**Database Schema**:
```cypher
MATCH (p:Post)
WHERE p.entity_matched IN ['tannar', 'loserfruit', 'fasffy', 'develique', 'oasis', 'nalopia', 'aliythia', 'berticuss']
RETURN p
```

**Tags to Apply**:
- `p.entity_matched = 'tannar'` - Entity name for tracking
- `p.entity_matched = 'loserfruit'` - Entity name for tracking
- `p.entity_matched = 'fasffy'` - Entity name for tracking
- `p.entity_matched = 'develique'` - Entity name for tracking
- `p.entity_matched = 'oasis'` - Entity name for tracking
- `p.entity_matched = 'nalopia'` - Entity name for tracking
- `p.entity_matched = 'aliythia'` - Entity name for tracking
- `p.entity_matched = 'berticuss'` - Entity name for tracking

### Future Development

1. **Facial Recognition Integration**
   - Extract images from posts tagged with entities
   - Run facial recognition to detect entity appearance
   - Create `(:Entity)-[:APPEARS_IN]->(:Post)` relationships

2. **Keyword Detection**
   - Pattern matching on post titles and selftext
   - Auto-tag posts with entity_matched field
   - Case-insensitive search for entity names

3. **Entity Graph**
   - Create `(:Entity {name: 'Tannar'})` node
   - Create nodes for all 8 entities
   - Link posts: `(:Entity)-[:MENTIONED_IN]->(:Post)`
   - Track appearance frequency over time

4. **Cross-Subreddit Tracking**
   - Search for entity mentions across other subreddits
   - Target subreddits:
     - r/Models
     - r/offlinetvGirls
     - r/VolleyballGirls
     - r/Taylorhillfantasy
     - r/BrookeMonkTheSecond
     - r/BestOfBrookeMonk

### Monitoring Setup

**Monitored Subreddits with Entity Tags**:
- r/sunisalee: entity_matched=sunisa lee (Olympic athlete)
- r/TOS_girls: 8 entities (TOS fandom girls)
  - Tannar, Loserfruit, Fasffy, Develique, Oasis, Nalopia, Aliythia, Berticuss

**Total Entity-Mapped Posts**: 41+
- Sunisa Lee: 1 posts
- Fasffy: 2 posts
- TOS girls: 30 posts
- Future: Expand to other entities

### Notes
- Subreddit naming: Welcome message mentions "r/TOS_girls" with "g" not "irl"
- Welcome post lists: Tannar, Loserfruit, Fasffy, Develique, Oasis, Nalopia, Aliythia, Berticuss
- All entities are female creators/influencers from TOS fandom
- Entity mapping enables cross-subreddit tracking and facial recognition
- High engagement posts: Multiple posts with 30+ score

### Related Entity Mappings
- ENTITY_MAPPING_FASFFY.md - Fasffy specific tracking
- ENTITY_MAPPING_SUNISA_LEE.md - Sunisa Lee Olympic athlete tracking
- Future: Create ENTITY_MAPPING_TOS_GIRLS.md for all 8 entities

### Sample Posts Indexed
- Fasffy (1pumqy0, 1pwmwc5): 29 score
- Loserfruit (1px3g9r): 32 score, 2 images
- Tannar (1pu1hff): 21 score
- Develique (multiple): 24-47 score
- Oasis (1ptqe72): 16 score
- Aliythia (1pyipuo): 40 score
- Berticuss (1q1wz1e, 1py6t79): 45-62 score

### Performance Metrics
- Entity matching rate: 92% (92/100 posts contain entity names)
- Image caching rate: ~35% (11 images from 30 posts)
- Slow mode delays: 5-10s between requests (rate limit respectful)
- Database indexing: MERGE on post ID to avoid duplicates
