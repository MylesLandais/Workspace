# Creator/Handle/Media Ontology Implementation

This document describes the implementation of the core application system ontology and business logic for entity resolution and cross-platform media aggregation.

## Overview

The system implements a knowledge graph-based approach to:
1. **Entity Resolution**: Unify multiple social media accounts (handles) under a single Creator identity
2. **Cross-Platform Discovery**: Automatically discover handles from anchor URLs (bio-crawler)
3. **Media Normalization**: Standardize content from different platforms into a unified Media format
4. **Omni-Feed Aggregation**: Combine content from all verified handles into a single chronological feed

## Architecture

### Graph Database Schema (Neo4j)

#### Node Types

- **Creator**: Canonical identity representing a person/brand
  - Properties: `uuid`, `name`, `slug`, `bio`, `avatar_url`, `created_at`, `updated_at`
  - Constraints: `uuid` and `slug` are unique

- **Handle**: Platform-specific account
  - Properties: `uuid`, `username`, `display_name`, `profile_url`, `follower_count`, `verified_by_platform`
  - Constraints: `uuid` is unique

- **Platform**: Social media platform
  - Properties: `name`, `slug`, `api_base_url`, `icon_url`
  - Constraints: `name` and `slug` are unique

- **Media**: Normalized content (base label)
  - Properties: `uuid`, `title`, `source_url`, `publish_date`, `thumbnail_url`, `media_type`
  - Auxiliary labels: `:Video`, `:Image`, `:Text` (for polymorphism)
  - Video-specific: `duration`, `view_count`, `aspect_ratio`, `resolution`
  - Image-specific: `width`, `height`, `aspect_ratio`
  - Text-specific: `body_content`, `word_count`

#### Relationship Types

- **OWNS_HANDLE**: `(Creator)-[:OWNS_HANDLE]->(Handle)`
  - Properties: `status` (Active/Suspended/Abandoned/Unverified), `verified`, `confidence`, `discovered_at`, `verified_at`
  - Represents ownership and verification state

- **ON_PLATFORM**: `(Handle)-[:ON_PLATFORM]->(Platform)`
  - Structural connection indicating which platform a handle belongs to

- **REFERENCES**: `(Handle)-[:REFERENCES]->(Handle)`
  - Soft connection for bio-crawler discoveries
  - Properties: `source_url`, `discovered_at`, `confidence`, `context`
  - Tracks how handles were discovered

- **PUBLISHED**: `(Handle)-[:PUBLISHED]->(Media)`
  - Properties: `published_at`, `engagement_score`
  - Links handles to their content

- **SOURCED_FROM**: `(Media)-[:SOURCED_FROM]->(Platform)`
  - Platform attribution for media

## Components

### 1. Ontology Schema (`src/feed/ontology/schema.py`)

Defines the graph structure, node properties, relationship types, and validation logic.

**Key Classes:**
- `GraphOntology`: Central schema definition
- `HandleStatus`: Enum for handle status (Active, Suspended, Abandoned, Unverified)
- `VerificationConfidence`: Enum for confidence levels (High, Medium, Manual)
- `MediaType`: Enum for media types (Video, Image, Text, Audio, Mixed)

### 2. Data Models (`src/feed/models/`)

Pydantic models for type safety and validation:

- **Creator** (`creator.py`): Canonical identity model
- **Handle** (`handle.py`): Platform-specific account model
- **Platform** (`platform.py`): Platform model
- **Media** (`media.py`): Base media model with specialized subclasses:
  - `VideoMedia`: Video-specific properties
  - `ImageMedia`: Image-specific properties
  - `TextMedia`: Text-specific properties

### 3. Services (`src/feed/services/`)

Business logic services:

#### BioCrawler (`bio_crawler.py`)
- Discovers handles from anchor URLs (e.g., YouTube About page)
- Parses HTML for social media links using regex patterns
- Supports: Instagram, TikTok, Twitter/X, YouTube, Reddit, Facebook, LinkedIn
- Returns `CandidateHandle` objects with confidence levels

#### VerificationService (`verification.py`)
- Manages handle verification state
- Updates handle status (Active/Suspended/Abandoned)
- Infers confidence from username matching across platforms
- Retrieves unverified handles for review

#### CreatorService (`creator_service.py`)
- Creates and manages Creator entities
- Adds handles to creators with platform relationships
- Ensures unique slugs (auto-generates variations if needed)
- Integrates bio-crawler for handle discovery

### 4. Platform Adapters (`src/feed/platforms/media_adapters.py`)

Normalizes platform-specific API responses to standard Media format:

- **YouTubeAdapter**: Normalizes YouTube video data
- **TikTokAdapter**: Normalizes TikTok video data
- **InstagramAdapter**: Normalizes Instagram posts (images/videos)
- **RedditAdapter**: Normalizes Reddit posts (text/images/videos)

Each adapter implements:
- `normalize(raw_data)`: Converts platform JSON to Media object
- `get_platform_name()`: Returns platform name
- `get_platform_slug()`: Returns platform slug

### 5. GraphQL Schema (`src/feed/graphql/creator_schema.py`)

Extended GraphQL API for Creator/Handle/Media system:

**Types:**
- `CreatorType`: Creator with nested handles
- `HandleType`: Handle with platform info
- `Media`: Normalized media with platform attribution
- `Platform`: Platform metadata
- `CandidateHandle`: Discovered handle candidate

**Queries:**
- `creator(slug: String)`: Get creator by slug with all handles
- `creators(limit, offset)`: List creators
- `feed(creator_id, filter)`: Get aggregated omni-feed

**Filters:**
- `exclude_platforms`: Exclude specific platforms from feed
- `media_types`: Filter by media type
- `limit`/`offset`: Pagination

### 6. Database Migration (`src/feed/storage/migrations/002_creator_handle_media_schema.cypher`)

Cypher migration script that:
- Creates constraints for uniqueness
- Creates indexes for query performance
- Documents node and relationship structures
- Includes example query patterns

## Usage Examples

### Creating a Creator

```python
from src.feed.services.creator_service import CreatorService

service = CreatorService()
creator = service.create_creator(
    name="Eefje Depoortere",
    slug="sjokz",
    bio="Esports host and presenter",
)
```

### Discovering Handles

```python
from src.feed.services.bio_crawler import BioCrawler

crawler = BioCrawler()
candidates = crawler.discover_handles("https://www.youtube.com/@sjokz/about")

for candidate in candidates:
    print(f"Found: {candidate.username} on {candidate.platform}")
    print(f"Confidence: {candidate.confidence}")
```

### Normalizing Media

```python
from src.feed.platforms.media_adapters import get_adapter_for_platform

adapter = get_adapter_for_platform("youtube")
media = adapter.normalize(youtube_api_response)
print(f"Normalized: {media.title} ({media.media_type})")
```

### GraphQL Query

```graphql
query {
  creator(slug: "sjokz") {
    uuid
    name
    slug
    handles {
      username
      platform {
        name
        slug
      }
      verified
      status
    }
  }
  
  feed(creatorId: "sjokz", filter: {
    excludePlatforms: ["Reddit"]
    limit: 20
  }) {
    title
    sourceUrl
    publishDate
    mediaType
    platformName
    platformIconUrl
    duration
    viewCount
  }
}
```

## Verification & Confidence System

### Confidence Levels

1. **High**: Link found in trusted section (About, Bio, Contact)
2. **Medium**: Username matches across platforms or found in general content
3. **Manual**: Admin/user confirmed (100% confidence)

### Verification Workflow

1. Bio-crawler discovers handles → marked as `verified: false`
2. System infers confidence from username matching
3. Admin reviews unverified handles
4. Admin verifies handle → `verified: true`, `status: Active`
5. Only verified, active handles are used for media ingestion

### Handle Status

- **Active**: Handle is active and verified
- **Suspended**: Handle is suspended/banned
- **Abandoned**: Handle is no longer used
- **Unverified**: Handle discovered but not yet verified

## Graph Hygiene

### Soft Deletes

Handles are never deleted immediately. Instead:
- Status is updated to `Suspended` or `Abandoned`
- Historical analytics remain intact
- Ingestor skips suspended/abandoned handles

### Slug Canonicalization

- Slugs are auto-generated from names
- If slug exists, system appends suffix (e.g., `sjokz-csgo`)
- Ensures unique, URL-friendly identifiers

## Next Steps

1. **Run Migration**: Execute `002_creator_handle_media_schema.cypher` in Neo4j
2. **Seed Platforms**: Create Platform nodes for supported platforms
3. **Implement Ingestors**: Create workers to fetch and normalize media from APIs
4. **Build UI**: Create identity discovery wizard (Card 5) and visual source attribution (Card 6)
5. **Add More Platforms**: Extend adapters for additional platforms

## File Structure

```
src/feed/
├── ontology/
│   ├── __init__.py
│   └── schema.py              # Graph ontology definitions
├── models/
│   ├── creator.py             # Creator model
│   ├── handle.py              # Handle model
│   ├── platform.py            # Platform model
│   └── media.py               # Media models (base + specialized)
├── services/
│   ├── bio_crawler.py          # Handle discovery service
│   ├── verification.py        # Verification system
│   └── creator_service.py      # Creator management
├── platforms/
│   └── media_adapters.py      # Platform normalization adapters
├── graphql/
│   └── creator_schema.py      # Extended GraphQL schema
└── storage/
    └── migrations/
        └── 002_creator_handle_media_schema.cypher
```

## Dependencies

- `neo4j`: Graph database driver
- `strawberry-graphql`: GraphQL framework
- `pydantic`: Data validation
- `beautifulsoup4`: HTML parsing for bio-crawler
- `requests`: HTTP requests for bio-crawler








