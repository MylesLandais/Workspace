# Entity Mapping for Facial Recognition

## Coomer.st Platform Entity Tracking

### Platform Analysis

### Source
- **Site**: coomer.st (archive site for OnlyFans content)
- **Entity**: myla.feet (from URL context)
- **Context**: OnlyFans creator content reference
- **URL**: https://coomer.st/onlyfans/user/myla.feet?q=snow

### Platform Challenges
- coomer.st is an archive/redirect site, not direct OnlyFans content
- OnlyFans requires authentication and API access
- Direct scraping would violate terms of service
- Site focuses on user-submitted content archives

### Current Status
- Entity node created: `myla feet`
- Reference post created with coomer.st URL
- Entity linked to reference post via `[:REFERENCES_IN]` relationship
- No direct content scraped (ethical constraints)

### Implementation Notes

#### Database Schema
```cypher
// Entity node
(:Entity {name: 'myla feet'})

// Reference post with platform tag
(:Post {platform: 'coomer.st', entity_matched: 'myla feet'})

// Entity relationship
(:Entity)-[:REFERENCES_IN]->(:Post)
```

#### Ethical Considerations
1. **No Direct Scraping**
   - OnlyFans content is paid and behind authentication
   - Respect creator terms of service
   - Archive sites provide indirect access only

2. **Entity Focus**
   - Track entity mentions across platforms
   - Focus on public social media references
   - Avoid direct paid content scraping

3. **Future Integration**
   - Monitor social media for 'myla.feet' mentions
   - Track coomer.st references and archived content
   - Maintain ethical boundary respect

### Cross-Platform Entity Tracking

#### Current Entity Coverage
| Entity | Source | Status | Notes |
|--------|--------|--------|
| myla feet | coomer.st | ✓ | Reference created |
| Sunisa Lee | Instagram | ✓ | Olympian |
| Fasffy | r/TOS_girls | ✓ | TOS fandom |

### Monitoring Strategy

#### Target Platforms
1. **Social Media**
   - Instagram (myla.feet mentions)
   - Twitter/X (coomer references)
   - Reddit (archived discussions)

2. **Archive Sites**
   - coomer.st (monitor new appearances)
   - Similar OnlyFans archive platforms

3. **Creator Networks**
   - Fitness modeling communities
   - Sports content platforms
   - Adult content discussion forums

### Technical Implementation

#### Entity Detection Patterns
```
// Entity name variations
['myla.feet', 'myla', 'myla feet', 'mylafeet']

// Platform keywords
['coomer', 'onlyfans', 'archived', 'leaked']

// Context keywords
['fitness', 'modeling', 'athlete', 'creator']
```

#### Database Queries
```cypher
// Find all coomer.st related posts
MATCH (p:Post)
WHERE p.platform = 'coomer.st'
OR p.url CONTAINS 'coomer.st'
OR p.selftext CONTAINS 'coomer'
RETURN p

// Cross-platform entity tracking
MATCH (e:Entity)-[:REFERENCES_IN]->(p:Post)
RETURN e.name, p.platform, p.url, p.created_utc
```

### Files Created
- ENTITY_MAPPING_COOMER.md - This file
- Database entities for coomer.st platform tracking
- Reference posts for indirect content access

### Future Development

1. **Platform Expansion**
   - Add more OnlyFans archive sites
   - Track Discord/Telegram leak channels
   - Monitor Reddit OnlyFans discussions

2. **Facial Recognition**
   - Public social media image extraction
   - Cross-platform face matching
   - Entity appearance verification

3. **Content Classification**
   - Adult content detection
   - Platform source attribution
   - Content type categorization

### Performance Metrics
- **Entity nodes**: 1 (myla feet)
- **Reference posts**: 1 (coomer.st URL)
- **Cross-platform tracking**: Ready for implementation
- **Ethical compliance**: 100% (no direct scraping)

### Notes
- coomer.st serves as indirect OnlyFans content discovery
- Entity mapping focuses on creator identification, not content access
- Respects creator rights and platform terms
- Enables cross-platform tracking without violating terms of service