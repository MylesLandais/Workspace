# Entity Metadata Sources & Schema

## Status

Accepted

## Context

Creator/entity profiles need rich metadata beyond basic name and bio. Multiple sources provide structured data that can be aggregated to build comprehensive profiles:
- Wikipedia infobox templates (structured, authoritative)
- Google Knowledge Panels (aggregated, cross-platform)
- Platform-specific profiles (Instagram, YouTube, etc.)
- Specialized sites (WikiFeet, IMDb, etc.)

## Decision

Adopt a Wikipedia infobox-inspired schema for Creator metadata, with support for multiple data sources and confidence scoring.

## Rationale

**Wikipedia Infobox Pattern**: Proven schema for person profiles across domains. Handles edge cases and scales to many entity types.

**Multi-Source Aggregation**: Different sources provide different data (WikiFeet has physical stats, Wikipedia has career info, Instagram has real-time updates).

**Confidence Scoring**: Not all sources are equally reliable. Track source and confidence for each field.

**Extensibility**: Schema can grow without breaking existing queries.

## Implementation

### Enhanced Creator Schema

```cypher
CREATE (c:Creator {
  id: "sjokz",
  slug: "sjokz",
  name: "Eefje Depoortere",
  displayName: "Sjokz",
  bio: "Belgian television presenter, reporter, and esports player",
  
  // Personal Information
  birthDate: date("1987-06-16"),
  birthPlace: "Bruges, Belgium",
  nationality: "Belgian",
  height: "1.73 m",  // or "5'8""
  heightCm: 173,
  
  // Career
  occupation: ["Television presenter", "Reporter", "Esports player"],
  employer: ["Riot Games", "Electronic Sports League"],
  education: ["Ghent University"],
  degrees: ["Master's in History", "Sports Journalism", "Teaching degree"],
  
  // Social Stats (aggregated)
  totalFollowers: 2000000,  // Sum across all platforms
  primaryPlatform: "Instagram",
  
  // Metadata
  verified: true,
  dataSources: ["wikipedia", "instagram", "youtube"],
  lastUpdated: datetime()
})
```

### Data Source Tracking

Track where each piece of metadata came from:

```cypher
// Create metadata source relationships
CREATE (c:Creator {id: "sjokz"})
CREATE (w:DataSource {
  type: "wikipedia",
  url: "https://en.wikipedia.org/wiki/Sjokz",
  lastCrawled: datetime(),
  confidence: "high"
})
CREATE (i:DataSource {
  type: "instagram",
  url: "https://www.instagram.com/eefjah/",
  lastCrawled: datetime(),
  confidence: "high"
})

CREATE (c)-[:METADATA_FROM {
  field: "birthDate",
  value: "1987-06-16",
  confidence: "high",
  lastUpdated: datetime()
}]->(w)

CREATE (c)-[:METADATA_FROM {
  field: "followerCount",
  value: "548300",
  confidence: "high",
  lastUpdated: datetime()
}]->(i)
```

### Wikipedia Infobox Mapping

Map Wikipedia infobox fields to our schema:

| Wikipedia Field | Creator Property | Example |
|----------------|------------------|---------|
| `birth_name` | `name` | "Eefje Depoortere" |
| `birth_date` | `birthDate` | date("1987-06-16") |
| `birth_place` | `birthPlace` | "Bruges, Belgium" |
| `height` | `height` | "1.73 m" |
| `occupation` | `occupation` | ["Television presenter", ...] |
| `employer` | `employer` | ["Riot Games", ...] |
| `alma_mater` | `education` | ["Ghent University"] |
| `television` | `television` | ["League of Legends European Championship"] |

### Google Knowledge Panel Pattern

Google aggregates from multiple sources. We can replicate this:

```cypher
// Aggregate stats from all handles
MATCH (c:Creator {id: $creatorId})-[r:OWNS_HANDLE]->(h:Handle)
WHERE r.status = "active"
WITH c, sum(h.followerCount) AS totalFollowers, 
     collect({platform: h.platform, count: h.followerCount}) AS platformStats
SET c.totalFollowers = totalFollowers,
    c.platformStats = platformStats
RETURN c
```

## Data Sources

### Wikipedia
- **URL Pattern**: `https://en.wikipedia.org/wiki/{name}`
- **Data**: Birth date, occupation, education, career highlights
- **Confidence**: High (curated, verified)
- **Update Frequency**: Periodic (when Wikipedia updates)

### Instagram
- **URL Pattern**: `https://www.instagram.com/{username}/`
- **Data**: Follower count, bio, recent posts, profile picture
- **Confidence**: High (official account)
- **Update Frequency**: Real-time (via API)

### Google Knowledge Panel
- **URL Pattern**: Search result (not directly crawlable)
- **Data**: Aggregated stats, related people, quick facts
- **Confidence**: Medium (aggregated, may have errors)
- **Update Frequency**: Google's crawl schedule

### WikiFeet / Specialized Sites
- **URL Pattern**: `https://wikifeet.com/{name}`
- **Data**: Physical stats (height, shoe size), ratings
- **Confidence**: Medium (user-contributed, may be inaccurate)
- **Update Frequency**: User-contributed

## Consequences

**Positive**:
- Rich, comprehensive profiles
- Multiple sources provide redundancy
- Confidence scoring helps with data quality
- Wikipedia pattern is well-established

**Negative**:
- More complex schema
- Need crawlers for each source
- Data conflicts require resolution logic
- Some sources may be unreliable

**Neutral**:
- Can start with basic fields, add more over time
- Confidence scoring allows gradual improvement

## Implementation Notes

- Start with high-confidence sources (Wikipedia, official platforms)
- Add specialized sources (WikiFeet) as optional enrichment
- Track data source for auditability
- Implement conflict resolution (prefer Wikipedia over user-contributed)
- Cache crawled data to avoid rate limits
- Respect robots.txt and rate limits

## References

- Wikipedia: Infobox person template
- Google Knowledge Graph API (if available)
- Platform APIs (Instagram Graph API, etc.)






