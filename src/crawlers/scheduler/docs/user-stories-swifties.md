# User Stories: Swifties Following Taylor Swift Everywhere

## Overview
This document captures user stories for tracking Taylor Swift content across multiple platforms and sources, specifically for Swifties who want to follow Taylor Swift content everywhere it appears.

## User Stories

### US-001: Track Taylor Swift Across Multiple Reddit Sources
**As a** Swiftie  
**I want to** see all Taylor Swift content from multiple Reddit subreddits in one place  
**So that** I don't miss any posts about her across different communities

**Acceptance Criteria:**
- System tracks multiple Reddit subreddits as sources for Taylor Swift content
- Subreddits are linked to the Taylor Swift Creator entity
- Posts from all tracked subreddits are discoverable through the Creator entity
- New subreddits can be added dynamically

**Example Subreddits:**
- r/TaylorSwiftPictures
- r/TaylorSwift
- r/TaylorSwiftCandids
- r/TaylorSwiftMidriff

### US-002: Tag Posts by Taylor Swift Era
**As a** Swiftie  
**I want to** filter and search posts by Taylor Swift era  
**So that** I can find content from specific eras (e.g., TLOAS, Folklore, Midnights)

**Acceptance Criteria:**
- Posts can be tagged with era information
- Era tags include both short code (e.g., "TLOAS") and full name (e.g., "The Tortured Poets Department")
- Posts can be queried by era
- Era information is preserved when posts are stored

**Known Eras:**
- TLOAS: The Tortured Poets Department
- Folklore: Folklore
- Evermore: Evermore
- Midnights: Midnights
- Red: Red (Taylor's Version)
- 1989: 1989 (Taylor's Version)
- Reputation: Reputation
- Lover: Lover
- And more...

### US-003: Automatic Content Discovery
**As a** Swiftie  
**I want to** automatically discover new Taylor Swift content as it's posted  
**So that** I stay up-to-date with the latest posts

**Acceptance Criteria:**
- System monitors tracked subreddits for new posts
- New posts are automatically linked to the Taylor Swift Creator entity
- Posts are automatically tagged with era when possible
- Notification system alerts users to new content (future enhancement)

### US-004: Cross-Platform Content Aggregation
**As a** Swiftie  
**I want to** see Taylor Swift content from multiple platforms (Reddit, Twitter, Instagram, etc.)  
**So that** I have a comprehensive view of all her content

**Acceptance Criteria:**
- Creator entity can have sources from multiple platforms
- Posts from different platforms are linked to the same Creator entity
- Platform information is preserved in relationships
- Content can be filtered by platform

### US-005: Era-Based Content Browsing
**As a** Swiftie  
**I want to** browse all content from a specific era  
**So that** I can relive or explore specific periods of Taylor Swift's career

**Acceptance Criteria:**
- Query interface supports filtering by era
- Results show posts from all tracked sources for that era
- Era information is displayed clearly
- Content can be sorted by date within an era

### US-006: Crawler URL Index and Deduplication
**As a** crawler operator  
**I want to** check if a URL has been processed before  
**So that** I can avoid duplicate processing and track what's been crawled

**Acceptance Criteria:**
- System maintains an index of processed URLs
- Can check if a single URL has been seen
- Can batch check multiple URLs
- Returns post details if URL has been processed
- Supports crawler monitoring and resumption

### US-007: Crawler Session Tracking
**As a** crawler operator  
**I want to** know when the crawler last ran and estimate backlog  
**So that** I can plan resumption after a hiatus

**Acceptance Criteria:**
- System tracks last crawl time per subreddit
- Estimates time since last crawl
- Estimates number of new posts since last crawl
- Estimates requests needed to catch up
- Shows last processed post details

### US-008: Resume Crawling After Hiatus
**As a** crawler operator  
**I want to** resume crawling after a break  
**So that** I can catch up on missed content efficiently

**Acceptance Criteria:**
- System shows what's been missed since last crawl
- Estimates work needed to catch up
- Can process new posts incrementally
- Avoids re-processing already crawled content
- Handles errors gracefully to allow resumption

### US-009: Cache Hit Checking for Crawler
**As a** crawler operator  
**I want to** check if a post is already in the database before fetching  
**So that** I can avoid unnecessary API requests and duplicate processing

**Acceptance Criteria:**
- System checks Neo4j database before fetching from Reddit API
- Returns full metadata if post exists (cache hit)
- Only fetches from API if post not found (cache miss)
- Supports batch cache checking for multiple URLs
- Can update existing posts (e.g., add era tags) without re-fetching
- Metadata is stored in Neo4j, not local files (single source of truth)

## Implementation Notes

### Database Schema
- `Creator` nodes represent Taylor Swift
- `Subreddit` nodes represent Reddit communities
- `Post` nodes represent individual posts
- `HAS_SOURCE` relationship: `(Creator)-[:HAS_SOURCE]->(Subreddit)`
- `ABOUT` relationship: `(Post)-[:ABOUT]->(Creator)`
- `Post.era` property: Short era code (e.g., "TLOAS")
- `Post.era_full_name` property: Full era name (e.g., "The Tortured Poets Department")

### Example Queries

#### Find all posts about Taylor Swift from a specific subreddit:
```cypher
MATCH (c:Creator {slug: 'taylor-swift'})-[:HAS_SOURCE]->(s:Subreddit {name: 'TaylorSwiftPictures'})
MATCH (p:Post)-[:POSTED_IN]->(s)
MATCH (p)-[:ABOUT]->(c)
RETURN p.id, p.title, p.created_utc, p.era
ORDER BY p.created_utc DESC
```

#### Find all posts from a specific era:
```cypher
MATCH (p:Post {era: 'TLOAS'})-[:ABOUT]->(c:Creator {slug: 'taylor-swift'})
RETURN p.id, p.title, p.subreddit, p.created_utc
ORDER BY p.created_utc DESC
```

#### Find all subreddits tracking Taylor Swift:
```cypher
MATCH (c:Creator {slug: 'taylor-swift'})-[:HAS_SOURCE]->(s:Subreddit)
RETURN s.name, s.created_at
ORDER BY s.name
```

## Architecture

For detailed information about the spider architecture and design decisions, see [SPIDER_DESIGN_DECISIONS.md](./SPIDER_DESIGN_DECISIONS.md).

## Future Enhancements

1. **Automatic Era Detection**: Use ML to automatically detect era from post content/images
2. **Era Timeline Visualization**: Show posts on a timeline organized by era
3. **Cross-Reference Detection**: Automatically link related posts across subreddits
4. **Image Similarity**: Group similar images across different posts/eras
5. **Fan Community Tracking**: Track which subreddits are most active for each era
6. **Notification System**: Alert users when new content is posted in specific eras
7. **Crawl State Persistence**: Store exact crawl state for precise resumption
8. **Adaptive Rate Limiting**: Adjust delays based on API response times
9. **Parallel Processing**: Process multiple posts concurrently (with rate limiting)
10. **Incremental Updates**: Only fetch posts newer than last crawl timestamp
11. **Crawl Scheduling**: Automatic periodic crawls
12. **Health Monitoring**: Monitor crawler health and alert on issues

