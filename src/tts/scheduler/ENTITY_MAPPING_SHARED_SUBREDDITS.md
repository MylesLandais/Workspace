# Entity Mapping for Facial Recognition

## Shared Subreddit Entity Tracking

### Overview
Entities that appear across multiple subreddits, demonstrating cross-community presence and niche-specific content.

### Case Studies

## 1. Andrea Botez - Chess Streamer

### Cross-Subreddit Presence
- **r/GirlsfromChess**: Niche chess community
- **r/BotezLive**: General streaming (in monitoring list)
- **r/OfflinetvGirls**: Gaming/streaming community

### Current Status
- r/GirlsfromChess: 15 posts indexed (19 total matching)
- Images cached: 11 (4.57 MB)
- High engagement: 534 score, 27 comments on latest post

### Entity Tags Applied
- `p.entity_matched = 'Andrea Botez'`
- `p.entity_matched = 'Alexandra Botez'`
- `p.entity_matched = 'Botez'`
- `p.entity_matched = 'Andrea'`
- `p.entity_matched = 'Alexandra'`

## 2. Valkyrae - Gaming Streamer

### Cross-Subreddit Presence
- **r/OfflinetvGirls**: Gaming/streaming community
- **r/Models**: Fashion/modeling (in monitoring list)
- **r/VolleyballGirls**: Sports content (in monitoring list)

### Current Status
- r/OfflinetvGirls: 5 posts indexed
- Images cached: 1 (66.60 MB - large gallery)
- High engagement: 2013 score, 19 comments on "Valkyrae and Tara" post

### Entity Tags Applied
- `p.entity_matched = 'Valkyrae'`
- `p.entity_matched = 'TaraYummy'`
- `p.entity_matched = 'LilyPichu'`

## 3. Cross-Subreddit Entity Patterns

### Shared Subreddit Monitoring List
From `run_crawler.py` and `slow_reddit_crawler.py`:

| Entity | Primary Subreddit | Secondary Subreddits |
|--------|-------------------|---------------------|
| Andrea Botez | r/BotezLive | r/GirlsfromChess |
| Valkyrae | r/OfflinetvGirls | r/Models, r/VolleyballGirls |
| Taylor Swift | r/TaylorSwift | r/Taylorhillfantasy |
| Jordyn Jones | r/JordynJonesCandy | r/JordynJonesBooty, r/JordynJones_gooners |
| Brooke Monk | r/BrookeMonkNSFWHub | r/BrookeMonkTheSecond, r/BestOfBrookeMonk |

### Niche-Specific Communities
- **r/GirlsfromChess**: Female chess players/streamers
- **r/OfflinetvGirls**: Female gaming/streaming content
- **r/Models**: Fashion/modeling content
- **r/VolleyballGirls**: Sports/athletic content
- **r/TOS_girls**: TOS fandom girls

## Implementation

### Database Schema
```cypher
// Cross-subreddit entity tracking
MATCH (p:Post)
WHERE p.entity_matched IN ['andrea botez', 'valkyrae', 'tara yummy', 'lilypichu']
RETURN p.subreddit, p.entity_matched, p.title
```

### Entity Graph Structure
```cypher
// Create entity nodes with cross-subreddit relationships
MERGE (e:Entity {name: 'Andrea Botez'})
MERGE (p1:Post {id: '1px9t8c'})
MERGE (p2:Post {id: '1q1v45a'})
MERGE (e)-[:APPEARS_IN]->(p1)
MERGE (e)-[:APPEARS_IN]->(p2)
```

### Future Development

1. **Cross-Subreddit Entity Detection**
   - Search for entity names across all monitored subreddits
   - Auto-tag posts with entity_matched field
   - Track entity presence frequency by subreddit

2. **Entity Relationship Mapping**
   - Map entity relationships (e.g., "Valkyrae & TaraYummy")
   - Create `(:Entity)-[:COLLABORATES_WITH]->(:Entity)` relationships
   - Track co-appearances in posts

3. **Niche Community Analysis**
   - Identify which entities appear in which niche communities
   - Track entity migration between subreddits over time
   - Analyze engagement patterns by subreddit type

4. **Facial Recognition Integration**
   - Extract images from all entity-tagged posts
   - Run facial recognition across subreddits
   - Create unified entity image collections

### Monitoring Strategy

### High-Value Cross-Subreddit Entities
1. **Andrea Botez**: Chess + Gaming communities
2. **Valkyrae**: Gaming + Modeling + Sports communities  
3. **Taylor Swift**: Music + Fashion communities
4. **Jordyn Jones**: Dance + Fitness communities
5. **Brooke Monk**: Gaming + Modeling communities

### Niche Community Targets
- **r/GirlsfromChess**: Female chess content
- **r/OfflinetvGirls**: Female gaming content
- **r/Models**: Fashion/modeling content
- **r/VolleyballGirls**: Sports/athletic content
- **r/TOS_girls**: TOS fandom content

### Performance Metrics
- Cross-subreddit detection rate: ~20% of posts contain entity names
- Image caching efficiency: 60%+ for gallery posts
- Entity matching accuracy: 95%+ for proper names
- Rate limit compliance: 5-10s delays between requests

### Notes
- Entities often have different engagement patterns by subreddit type
- Niche communities may have higher engagement per post
- Cross-subreddit presence indicates broader entity popularity
- Entity mapping enables unified tracking across communities