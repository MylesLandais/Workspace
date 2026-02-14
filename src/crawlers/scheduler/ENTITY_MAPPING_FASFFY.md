# Entity Mapping for Facial Recognition

## FASFFY Entity Tracking

### Source
- **Subreddit**: r/TOS_irls
- **Entity**: Fasffy
- **Target**: Track posts where entity "fasffy" appears

### Current Status
- Post 1pumqy0 ("Fasffy") indexed with `entity_matched=fasffy`
- Image cached: 19283e3957d854a06290a32dd33049a1e1a73fb3d1c1d509141adf29eebdfa68.jpeg (63.1 KB)
- Subreddit: r/TOS_girls (note: user mentions TOS_irls in one place, TOS_girls in another)

### Implementation

**Database Schema**:
```cypher
MATCH (p:Post)
WHERE p.entity_matched = 'fasffy'
RETURN p
```

**Tags to Apply**:
- `p.entity_matched = 'fasffy'` - Entity name for tracking

### Future Development

1. **Facial Recognition Integration**
   - Extract images from posts tagged with fasffy
   - Run facial recognition to detect entity appearance
   - Create `(:Entity)-[:APPEARS_IN]->(:Post)` relationships

2. **Keyword Detection**
   - Pattern matching on post titles and selftext
   - Auto-tag posts with entity_matched field
   - Case-insensitive search: "fasffy"

3. **Entity Graph**
   - Create `(:Entity {name: 'Fasffy'})` node
   - Link posts: `(:Entity)-[:MENTIONED_IN]->(:Post)`
   - Track appearance frequency over time

### Monitoring Setup

**Existing Monitored Subreddits** (from run_crawler.py):
- TOS_girls (indexed: 1 post with fasffy tag)
- Models (indexed: 19 posts)
- victorious (indexed: 20 posts)
- Taylorhillfantasy (indexed: 1 post)
- lululemon (indexed: 40 posts)

### Notes
- r/TOS_irls only has 25 total posts, all from 2008-2017
- Subreddit may be deprecated or have low activity
- Primary source appears to be r/TOS_girls based on recent activity
