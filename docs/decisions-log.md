# Integration Decisions Log

This document tracks key decisions made during the integration of Bunny Feed and Reader Reader components, as well as other significant architectural and design decisions.

## React Version Upgrade

**Date**: Integration Planning Phase  
**Status**: Accepted  
**Impact**: Frontend dependencies

**Decision**: Upgrade Bunny frontend from React 18 to React 19.

**Rationale**:
- Team policy encourages running latest stable versions
- Provides forward compatibility with React ecosystem
- Enables use of React 19 features from Bunny codebase
- React 19 includes performance improvements and new features

**Implementation**: Updated `app/frontend/package.json` to use React 19.2.3 and React DOM 19.2.3.

**Related Files**:
- `app/frontend/package.json`

---

## AI Integration Approach

**Date**: Integration Planning Phase  
**Status**: Accepted  
**Impact**: Architecture and feature roadmap

**Decision**: AI features are future/beta enhancements, not core features. Architecture should leave room for "magic" moments where AI enhances user experience. Next generation solution will integrate with agent development toolkit.

**Rationale**:
- AI generation is not a core requirement for MVP
- Architecture should support extensibility for AI enhancements
- Future integration with agent development toolkit planned
- Allows incremental AI feature rollout without blocking core functionality

**Implementation**:
- GraphQL schema includes AI extension points (summaries, tags, Q&A)
- Service layer designed for AI integration (LiteLLM abstraction)
- Defer AI features to future development phases
- Keep architecture flexible for AI integration without coupling

**Related ADRs**:
- [AI Agent Architecture](./architecture/adr/ai-agent-architecture.md)
- [Reading Assistant Features](./architecture/adr/reading-assistant-features.md)

---

## Multi-user Support

**Date**: Integration Planning Phase  
**Status**: Accepted  
**Impact**: Data model and API design

**Decision**: Multi-user support is required. Users need to track and configure views specific to their tastes, preferences, and reading patterns.

**Rationale**:
- Users require personalized views and preferences
- Boards, entities, collections, and preferences must be user-specific
- Design should support multi-tenancy from the start to avoid migration complexity
- Enables future collaborative features (shared boards, team libraries)

**Implementation**:
- Include `userId: String!` in all user-specific nodes (SavedBoard, SavedItem, UserPreferences, etc.)
- Design GraphQL queries/mutations with user context from authentication
- Implement user authentication/authorization middleware
- Index on `userId` for efficient user-specific queries
- User context passed through GraphQL resolver context

**Related ADRs**:
- [Neo4j Graph Database](./architecture/adr/neo4j-graph-database.md)

---

## Relationship Type Modeling

**Date**: Integration Planning Phase  
**Status**: Accepted  
**Impact**: Graph schema design

**Decision**: Use free-form strings for relationship types, keeping schema extensible for future normalization to enums if common patterns emerge.

**Rationale**:
- Team prefers type safety, but relationship types are beyond current domain expertise
- Free-form strings provide flexibility for evolving relationship semantics
- Can normalize to enum in future if common patterns emerge through usage
- Avoids premature optimization of relationship taxonomy

**Implementation**:
- Use `type: String!` property on `RELATED_TO` relationship in Neo4j
- Index on `type` property for query performance
- Document common relationship types as they emerge
- Consider enum migration if clear patterns emerge in usage data

**Related ADRs**:
- [Neo4j Graph Database](./architecture/adr/neo4j-graph-database.md)
- [Ontology Management](./architecture/adr/ontology-management.md)

---

## Board and FeedGroup Organizational Model

**Date**: Integration Planning Phase  
**Status**: Design Exploration  
**Impact**: Data model and user experience

**Decision**: Design exploration needed for organizational model. Traditional OPML folders are insufficient. Need to support entity/source selection as filters or channels/subscriptions.

**Rationale**:
- Boards (filter presets) and FeedGroups (source collections) both serve organizational purposes
- Need flexible model beyond traditional folder structure
- Should support modern use cases (channels, subscriptions, filters, smart collections)
- Users need multiple organizational dimensions (by source, by topic, by filter)

**Current State**:
- FeedGroups exist for source organization
- Boards concept from Bunny needs integration
- Exploring unified "Channel" model that supports both source collections and filter presets

**Next Steps**:
- See [Board/FeedGroup Design Exploration](./bunny-board-feedgroup-design.md)
- Validate unified Channel model with team
- Implement based on validated design

**Recommendation**: Use Channel model that supports both source collections and filter presets, with query-based smart collections.

**Related Documentation**:
- [Bunny Board/FeedGroup Design](./bunny-board-feedgroup-design.md)

---

## Image Pool Storage Structure

**Date**: Integration Planning Phase  
**Status**: Deferred  
**Impact**: Data model and query performance

**Decision**: Defer decision on image pool storage structure until usage patterns are clearer.

**Options Considered**:
- **URL Array**: Store as `imagePool: [String!]!` array property on Creator node (simpler, faster reads)
- **Media Nodes**: Store as separate Media nodes with `(:Creator)-[:HAS_IMAGE_POOL]->(:Media)` relationships (more flexible, supports relationships)

**Rationale**:
- Image pool feature is not yet implemented
- Usage patterns will inform optimal structure
- Can migrate from array to nodes if relationships needed later

**Implementation**: Start with URL array on Creator node for simplicity. Consider Media nodes migration if relationships (tagging, similarity, clustering) are needed.

**Related ADRs**:
- [Media Normalization](./architecture/adr/media-normalization.md)

---

## Board and Channel Sharing

**Date**: Integration Planning Phase  
**Status**: Deferred  
**Impact**: Feature roadmap

**Decision**: Defer board/channel sharing feature to future enhancement phase.

**Rationale**:
- Focus on core functionality first (ingestion, organization, reading)
- Sharing requires additional complexity (permissions, access control, collaboration)
- Can be added later if user demand emerges
- Core architecture supports multi-user, enabling future sharing features

**Future Considerations**:
- Permission model (read, write, admin)
- Public vs. private boards
- Team/organization workspaces
- Real-time collaboration features

**Related ADRs**:
- [Bunny Feed Integration](./architecture/adr/bunny-feed-integration.md)

---

## Mock Data Strategy for Frontend Development

**Date**: 2025-12-24  
**Status**: Accepted  
**Impact**: Development workflow and testing

**Decision**: Implement comprehensive mock data strategy using MSW (Mock Service Worker) with factory-based data generation from real scraped Reddit data stored in `/temp/mock_data/`.

**Rationale**:
- Frontend developers need to work independently without backend dependencies
- Real scraped data provides better edge case coverage than synthetic data
- Factory-based generation enables scalable testing (1k-10k items) without manual fixture creation
- Schema-based mocking ensures mock data matches GraphQL contract
- Enables parallel frontend/backend development

**Implementation**:
- MSW intercepts GraphQL requests when `PUBLIC_GRAPHQL_MOCK=true`
- Data loader transforms Reddit JSON to GraphQL schema format
- Supports lazy loading and caching for performance
- Pre-configured filter presets for common testing scenarios
- Factory functions for generating test data at scale

**Impact**:
- Frontend developers can work without backend/Neo4j setup
- Realistic testing with 6k+ posts from 65+ subreddits
- Better debugging with comprehensive logging
- Foundation for Storybook integration and E2E testing scenarios
- Faster development iteration cycles

**Related Documentation**:
- [ADR: Mock Data Strategy](./architecture/adr/mock-data-strategy.md)
- [Mock Data Guide](./domains/feed/mock-data-guide.md)
- [Mock Data User Stories](./domains/feed/mock-data-user-stories.md)
- [GraphQL Mock Data Generation](./domains/feed/graphql-mock-data-generation.md)

---

## Decision Review Process

Decisions should be reviewed:

- **When requirements change**: Revisit decisions that may be impacted
- **Before implementation**: Validate design explorations with team
- **Quarterly**: Review deferred decisions for prioritization
- **After incidents**: Assess if decisions contributed to issues

## Decision Status Legend

- **Accepted**: Decision is final and implemented or in progress
- **Design Exploration**: Decision is being explored, not yet finalized
- **Deferred**: Decision is deferred to future phase, tracked for planning

## Notes

- All decisions should be revisited if requirements change
- Design explorations should be validated with team before implementation
- Deferred decisions should be tracked for future planning
- Significant decisions should have corresponding ADRs


