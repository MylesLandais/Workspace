# Creator-Handle Data Model

Updated data model using Creator-Handle pattern instead of Entity-Source.

## Node Types

### Creator

Canonical identity for a person, brand, or organization.

**Properties**:
- `id` (string): Unique identifier (UUID)
- `slug` (string): URL-friendly identifier (must be unique, system-generated)
- `name` (string): Real/full name (e.g., "Eefje Depoortere")
- `displayName` (string): Public display name (e.g., "Sjokz")
- `bio` (string): Biography/description
- `avatarUrl` (string): Profile picture URL
- `verified` (boolean): Whether identity is verified

**Personal Information**:
- `birthDate` (date): Date of birth
- `birthPlace` (string): Place of birth (city, country)
- `nationality` (string): Nationality
- `height` (string): Height in readable format (e.g., "1.73 m" or "5'8"")
- `heightCm` (integer): Height in centimeters (for sorting/filtering)

**Career Information**:
- `occupation` (array of strings): Occupations (e.g., ["Television presenter", "Reporter"])
- `employer` (array of strings): Current/past employers
- `education` (array of strings): Educational institutions
- `degrees` (array of strings): Degrees earned

**Social Stats** (aggregated):
- `totalFollowers` (integer): Sum of followers across all platforms
- `primaryPlatform` (string): Platform with most followers
- `platformStats` (object): Per-platform follower counts

**Metadata**:
- `dataSources` (array of strings): Sources used (e.g., ["wikipedia", "instagram"])
- `lastUpdated` (datetime): When profile was last updated

**Indexes**:
- `Creator.id` (unique constraint)
- `Creator.slug` (unique constraint, for lookups)
- `Creator.birthDate` (for age calculations)

### Handle

Platform-specific account belonging to a Creator.

**Properties**:
- `id` (string): Unique identifier (UUID)
- `platform` (string): Platform name ("reddit", "youtube", "twitter", etc.)
- `username` (string): Platform username
- `handle` (string): Platform-specific handle format (e.g., "@sjokz", "r/Sjokz")
- `url` (string): Full URL to the account
- `channelId` (string): Platform-specific ID (YouTube channel ID, etc.)
- `verified` (boolean): Whether this handle is verified
- `discoveredFrom` (string): Handle ID that led to discovery (for bio-crawler)

**Indexes**:
- `Handle.id` (unique constraint)
- `Handle.platform` (for platform filtering)
- `Handle.channelId` (for YouTube lookups)

### Platform

Platform node (Reddit, YouTube, Twitter, etc.).

**Properties**:
- `name` (string): Platform name
- `apiEndpoint` (string): API base URL
- `iconUrl` (string): Platform icon

### Media

Content item from a Handle (normalized across platforms).

**Properties**:
- `id` (string): Unique identifier
- `title` (string): Media title
- `sourceUrl` (string): Original platform URL
- `publishDate` (datetime): When content was published
- `thumbnail` (string): Thumbnail image URL
- `mediaType` (string): "video", "image", "text"
- `duration` (integer): Duration in seconds (videos only)
- `aspectRatio` (string): Aspect ratio (e.g., "16:9", "9:16")
- `viewCount` (integer): View count (if available)
- `platform` (string): Source platform

**Labels**:
- `:Media` (base label, all media)
- `:Video` (for videos, adds duration, viewCount)
- `:Image` (for images, adds width, height)
- `:Text` (for text posts, adds bodyContent)

## Relationships

### OWNS_HANDLE

`(Creator)-[:OWNS_HANDLE]->(Handle)`

Creator owns a platform account.

**Properties**:
- `status` (string): "active", "suspended", "abandoned"
- `verified` (boolean): Whether relationship is verified
- `verifiedAt` (datetime): When verification occurred
- `createdAt` (datetime): When handle was added

### ON_PLATFORM

`(Handle)-[:ON_PLATFORM]->(Platform)`

Handle exists on a platform.

**Properties**:
- `joinedAt` (datetime): When account was created
- `followerCount` (integer): Current follower count

### REFERENCES

`(Handle)-[:REFERENCES]->(Handle)`

Soft connection for discovery (bio-crawler found this connection).

**Properties**:
- `discoveredAt` (datetime): When connection was discovered
- `confidence` (string): "high", "medium", "low"
- `sourceUrl` (string): URL where link was found

### POSTED

`(Handle)-[:POSTED]->(Media)`

Handle posted this media item.

**Properties**:
- `postedAt` (datetime): When posted (may differ from Media.publishDate)

## Example Queries

### Get Creator with All Handles

```cypher
MATCH (c:Creator {slug: $slug})-[r:OWNS_HANDLE]->(h:Handle)
WHERE r.status = "active" AND r.verified = true
OPTIONAL MATCH (h)-[:ON_PLATFORM]->(p:Platform)
RETURN c, collect(h) AS handles, collect(p) AS platforms
```

### Get All Media for Creator (Unified Feed)

```cypher
MATCH (c:Creator {slug: $slug})-[r:OWNS_HANDLE {status: "active", verified: true}]->(h:Handle)
MATCH (h)-[:POSTED]->(m:Media)
WHERE m.publishDate >= datetime($since)
RETURN m
ORDER BY m.publishDate DESC
LIMIT $limit
```

### Bio-Crawler Discovery

```cypher
// Find candidate handles from anchor
MATCH (anchor:Handle {id: $anchorId})
MATCH (anchor)-[:REFERENCES]->(candidate:Handle)
WHERE candidate.verified = false
RETURN candidate
ORDER BY candidate.confidence DESC
```

### Verify Handle

```cypher
MATCH (c:Creator {id: $creatorId})
MATCH (h:Handle {id: $handleId})
MERGE (c)-[r:OWNS_HANDLE]->(h)
SET r.verified = true,
    r.verifiedAt = datetime(),
    r.status = "active",
    h.verified = true
RETURN r, h
```

## Migration from Entity-Source

```cypher
// Migrate Entity to Creator
MATCH (e:Entity)
CREATE (c:Creator {
  id: e.id,
  slug: toLower(replace(e.name, " ", "-")),
  name: e.name,
  displayName: e.name,
  verified: true
})

// Migrate Source to Handle
MATCH (s:Source)
CREATE (h:Handle {
  id: s.id,
  platform: s.source_type,
  username: COALESCE(s.subreddit_name, s.youtube_channel_handle),
  handle: CASE 
    WHEN s.source_type = "reddit" THEN "r/" + s.subreddit_name
    WHEN s.source_type = "youtube" THEN s.youtube_channel_handle
    ELSE s.name
  END,
  url: s.url,
  verified: true
})

// Migrate relationships
MATCH (e:Entity)-[:HAS_SOURCE]->(s:Source)
MATCH (c:Creator {id: e.id})
MATCH (h:Handle {id: s.id})
CREATE (c)-[:OWNS_HANDLE {status: "active", verified: true}]->(h)
```

