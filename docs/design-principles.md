# Core Design Principles

## Overview

This document defines the core design principles that guide architectural decisions, development practices, and user experience design for the Bunny platform. These principles are derived from competitive analysis and our unique graph-native architecture.

## Architecture Principles

### 1. Graph-Native First

**Principle**: Leverage Neo4j's graph structure as the primary data model. Relationships are first-class citizens, not afterthoughts.

**Implications**:
- Model data as nodes and relationships, not tables
- Use Cypher for queries that traverse relationships
- Design features that benefit from graph structure (citations, topics, recommendations)
- Prefer graph algorithms over application-level logic

**Examples**:
- Citation networks stored as `(:Item)-[:CITES]->(:Item)` relationships
- User reading patterns as `(:User)-[:READ]->(:Item)` graph
- Topic clustering using graph community detection algorithms
- Tag relationships (implications, aliases) as graph edges
- Visual similarity as `(:MediaItem)-[:SIMILAR_TO]->(:MediaItem)` relationships

**Related ADRs**:
- [Neo4j Graph Database](../architecture/adr/neo4j-graph-database.md)
- [Discovery Engine](../architecture/adr/discovery-engine.md)

### 2. Real-Time Responsiveness

**Principle**: Hot data paths must be sub-millisecond. Use Valkey for frequently accessed data, Neo4j for complex queries.

**Implications**:
- Cache reading progress, session state, and hot content in Valkey
- Use write-through and lazy loading patterns
- Real-time features via Valkey pub/sub
- Neo4j for complex graph queries and persistent storage

**Examples**:
- Reading progress updates go to Valkey first, sync to Neo4j periodically
- Feed content cached in Valkey with TTL
- Real-time annotations via pub/sub

**Related ADRs**:
- [Valkey Caching Layer](../architecture/adr/valkey-caching-layer.md)

### 3. AI Flexibility

**Principle**: AI capabilities should be flexible, cost-optimized, and provider-agnostic. Route tasks to appropriate models based on complexity.

**Implications**:
- Use LiteLLM for provider abstraction
- Route simple tasks to cheap models, complex tasks to capable models
- Cache AI responses to reduce costs
- Design agents with clear responsibilities

**Examples**:
- Tagging uses Gemini Flash ($0.075/1M tokens)
- Summarization uses Claude Haiku ($0.25/1M tokens)
- Complex Q&A uses Claude Sonnet ($3/1M tokens)
- Visual analysis uses CLIP embeddings for similarity
- Image tagging uses GPT-4V or Claude 3 Opus with vision

**Related ADRs**:
- [AI Agent Architecture](../architecture/adr/ai-agent-architecture.md)

### 4. Scalable by Design

**Principle**: Architecture must scale horizontally and handle growth gracefully. Optimize for Aura free tier limits while planning for scale.

**Implications**:
- Implement data archival strategies early
- Use Valkey to offload Neo4j
- Design for horizontal scaling (stateless services, queue-based processing)
- Monitor usage and optimize proactively

**Examples**:
- Archive old content to summary nodes
- Prune weak relationships
- Cache expensive graph queries

**Related ADRs**:
- [Neo4j Aura Optimization](../architecture/adr/neo4j-aura-optimization.md)

## Data Principles

### 5. Privacy-First

**Principle**: User data belongs to users. Minimize data collection, enable local-first options, and provide transparent controls.

**Implications**:
- Collect only necessary data
- Support local-only mode
- End-to-end encryption for sensitive data
- Easy data export and deletion
- No tracking without consent

**Examples**:
- Annotations encrypted client-side
- Optional analytics (opt-in)
- GDPR-compliant data handling

### 6. Content Deduplication

**Principle**: Same content from different sources should be stored once. Deduplicate aggressively across all sources.

**Implications**:
- Use Bloom filters for URL deduplication
- Content hash checking for text similarity
- Link duplicate items in graph
- Single source of truth per unique content

**Examples**:
- URL deduplication before ingestion
- Content hash checking for reposts
- Graph relationships link duplicates
- MD5 hash deduplication for media files
- Perceptual hashing for visual similarity detection

**Related ADRs**:
- [Unified Ingestion Layer](../architecture/adr/unified-ingestion-layer.md)

### 7. Relationship Preservation

**Principle**: Preserve context about how and why content was discovered. Maintain relationships that show content provenance.

**Implications**:
- Store discovery relationships (how user found content)
- Maintain citation networks
- Track source relationships
- Preserve annotation context

**Examples**:
- `(:User)-[:DISCOVERED_VIA]->(:Source)` relationships
- Citation chains preserved in graph
- Annotation relationships maintain context
- Tag relationships (implications, aliases) preserved in graph
- Visual similarity relationships stored as graph edges

### 8. Media and Text as Equal Content Types

**Principle**: Media (images, videos) and text content are first-class citizens. Both should have equal capabilities for organization, discovery, and annotation.

**Implications**:
- Media items stored with same graph structure as text items
- Tagging system works for both media and text
- Discovery features support both content types
- Boards/collections can contain mixed content
- Search works across all content types

**Examples**:
- Media items have same node structure as text items
- Tags apply to both media and text
- Visual similarity search complements text search
- Boards can contain articles and images

**Related ADRs**:
- [Media Tagging and Visual Search](../architecture/adr/media-tagging-visual-search.md)
- [Unified Ingestion Layer](../architecture/adr/unified-ingestion-layer.md)

### 9. Visual-First Discovery

**Principle**: Visual similarity and dimensional search are as important as text-based search for media content. Leverage both perceptual hashing and ML embeddings.

**Implications**:
- Support visual similarity search alongside tag search
- Dimensional filtering (width, height, aspect ratio) is essential
- Combine visual and tag signals for better discovery
- Cache visual embeddings for performance
- Use graph structure for visual similarity relationships

**Examples**:
- Perceptual hashing for fast similarity lookup
- ML embeddings (CLIP) for semantic visual understanding
- Dimensional search for specific use cases (wallpapers, thumbnails)
- Visual similarity stored as graph relationships

**Related ADRs**:
- [Media Tagging and Visual Search](../architecture/adr/media-tagging-visual-search.md)
- [Discovery Engine](../architecture/adr/discovery-engine.md)

### 10. Advanced Tagging System

**Principle**: Tags are hierarchical, relational, and categorized. Tag relationships (implications, aliases) enable powerful discovery beyond simple keyword matching.

**Implications**:
- Tags stored as graph nodes with relationships
- Support tag categories (character, artist, copyright, meta, style)
- Tag implications (character → series) as graph edges
- Tag aliases for common name variations
- Boolean tag search with exclusions
- Tag autocomplete with frequency and category

**Examples**:
- `(:Tag)-[:IMPLIES]->(:Tag)` for tag implications
- `(:Tag)-[:ALIAS_OF]->(:Tag)` for tag aliases
- `(:Tag)-[:IN_CATEGORY]->(:Category)` for categorization
- Boolean queries: "rem_(re:zero) width:1080 -nsfw"

**Related ADRs**:
- [Media Tagging and Visual Search](../architecture/adr/media-tagging-visual-search.md)

## User Experience Principles

### 11. Distraction-Free Reading

**Principle**: Reading interface should be clean, focused, and customizable. Remove distractions, enable customization.

**Implications**:
- Reader Mode style content cleaning
- Customizable themes (fonts, spacing, colors)
- Minimal UI during reading
- Keyboard shortcuts for power users

**Examples**:
- Clean HTML extraction
- Custom reading themes
- Full-screen reading mode

### 12. Seamless Cross-Device Experience

**Principle**: Users should be able to switch devices without losing context. Sync should feel instant and reliable.

**Implications**:
- Real-time progress sync
- Offline support with background sync
- Conflict resolution for simultaneous edits
- Consistent experience across platforms

**Examples**:
- Reading progress syncs in < 1 second
- Offline mode with background sync
- Annotations sync across devices

**Related ADRs**:
- [Reading Assistant Features](../architecture/adr/reading-assistant-features.md)

### 13. Intelligent Discovery

**Principle**: Help users discover relevant content through multiple signals, not just popularity. Leverage graph structure for context-aware recommendations.

**Implications**:
- Combine citation networks, topics, and user behavior
- Personalize based on reading graph
- Surface learning paths
- Explain why content is recommended

**Examples**:
- Citation-based recommendations
- Topic clustering for discovery
- Learning path suggestions
- Visual similarity recommendations
- Board-based discovery (Pinterest-style)
- Tag-based discovery with implications

**Related ADRs**:
- [Discovery Engine](../architecture/adr/discovery-engine.md)
- [Hybrid Search Architecture](../architecture/adr/hybrid-search-architecture.md)

### 14. Immersive Media Viewing

**Principle**: Media viewing should be immersive and gesture-friendly. Full-screen viewing, swipe navigation, and minimal chrome enable focus on content.

**Implications**:
- Full-screen immersive viewing (Scrolller-style)
- Gesture navigation (swipe between posts, double-tap to favorite)
- Minimal UI that appears on interaction
- Grid view with hover previews
- Quick actions without leaving feed
- Haptic feedback for mobile interactions

**Examples**:
- Full-screen image viewer
- Swipe gestures for navigation
- Hover zoom on thumbnails
- Quick-save without leaving feed
- Keyboard shortcuts for desktop

**Related ADRs**:
- [Media Tagging and Visual Search](../architecture/adr/media-tagging-visual-search.md)

## Development Principles

### 11. Domain-Driven Organization

**Principle**: Organize code and documentation by business domain, not technology. Domains are self-contained and well-documented.

**Implications**:
- Domain folders in codebase
- Domain documentation in `docs/domains/`
- Clear domain boundaries
- Domain experts own their domains

**Examples**:
- `docs/domains/feed/` for feed domain
- `docs/domains/subscriptions/` for subscription management
- Domain-specific ADRs

### 12. Documentation as Code

**Principle**: Documentation lives with code and is kept up-to-date. ADRs explain why, code comments explain how.

**Implications**:
- ADRs for architectural decisions
- README files in each domain
- Code examples in documentation
- Keep docs in sync with code

**Examples**:
- ADRs in `docs/architecture/adr/`
- Domain READMEs explain concepts
- Code examples in ADRs

### 13. Progressive Enhancement

**Principle**: Core functionality works without advanced features. Enhance with AI, real-time sync, and advanced features when available.

**Implications**:
- Basic reading works offline
- AI features are enhancements, not requirements
- Graceful degradation when services unavailable
- Core features don't depend on external services

**Examples**:
- Reading works without AI summarization
- Offline mode for core features
- Fallback when AI services unavailable

### 14. Leverage Open-Source

**Principle**: Prefer adapting proven open-source solutions over building from scratch. Evaluate existing projects before implementing new features. Faster development and reduced maintenance burden.

**Implications**:
- Research open-source solutions for complex features (facial recognition, image processing, etc.)
- Adapt and integrate existing open-source implementations where possible
- Contribute back to open-source projects when feasible
- Use open-source libraries and frameworks over proprietary solutions when they meet requirements
- Learn from open-source architecture patterns even if not directly using the code

**Examples**:
- Leverage Immich's facial recognition system for multi-subject image analysis
- Use open-source ML models and libraries (CLIP, face_recognition)
- Evaluate TypeScript/Node.js open-source projects first for easier integration
- Reference proven architectures from successful open-source projects
- Focus on integration and ontology-driven entity resolution (like Palantir's pattern) rather than building proprietary algorithms

**Related ADRs**:
- [Facial Recognition and Multi-Subject Image Analysis](../architecture/adr/facial-recognition-multi-subject.md)

## Integration Principles

### 15. Open Integration

**Principle**: Enable integrations with popular tools. Export data in standard formats. Provide APIs for custom integrations.

**Implications**:
- Export to note-taking apps (Obsidian, Notion, Roam)
- API for custom integrations
- Webhook support
- Standard formats (Markdown, JSON, OPML)

**Examples**:
- Readwise export for spaced repetition
- Obsidian plugin
- Zapier webhooks

### 16. Source Agnostic

**Principle**: Support any content source. Don't favor one source type over another. Unified ingestion for all sources.

**Implications**:
- RSS, scraping, email, extension, API all equal
- Consistent data model regardless of source
- No source-specific special cases in core logic

**Examples**:
- All sources normalize to Item format
- Same annotation system for all sources
- Unified search across all sources
- Media sources (Booru, Reddit) use same ingestion pipeline
- Text and media content in same graph structure

**Related ADRs**:
- [Unified Ingestion Layer](../architecture/adr/unified-ingestion-layer.md)

## Performance Principles

### 17. Cache Aggressively

**Principle**: Cache expensive operations. Use Valkey for hot data, cache AI responses, cache graph queries.

**Implications**:
- Cache AI summaries and embeddings
- Cache expensive graph queries
- Cache feed content
- Appropriate TTLs for different data types

**Examples**:
- AI summaries cached for 24 hours
- Graph recommendations cached for 5 minutes
- Feed content cached for 5 minutes

**Related ADRs**:
- [Valkey Caching Layer](../architecture/adr/valkey-caching-layer.md)

### 18. Optimize for Common Paths

**Principle**: Optimize the 80% case. Most users read content, not manage complex queries. Optimize reading experience first.

**Implications**:
- Fast feed loading
- Quick search results
- Instant progress sync
- Optimize reading interface performance

**Examples**:
- Feed queries optimized for common filters
- Search indexes on frequently queried fields
- Lazy loading for less common features

## References

- [Requirements](./requirements.md)
- [Architecture Decision Records](./architecture/adr/)
- Competitive Analysis: Readwise Reader, Feedly, RSS.app

