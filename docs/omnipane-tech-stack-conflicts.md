# OmniPane Tech Stack Conflicts and Integration Points

## Overview

This document identifies conflicts between OmniPane Reader's tech stack and Bunny's existing architecture, and proposes integration strategies.

## Tech Stack Comparison

### Frontend

| Component | OmniPane | Bunny | Conflict Level |
|-----------|----------|-------|----------------|
| Framework | React 19.2.3 + Vite | Astro + React 18.3.1 | Medium |
| State | React hooks + LocalStorage | GraphQL + Apollo Client | High |
| Styling | Tailwind CSS (implicit) | Tailwind CSS (installed) | Low |
| Icons | Lucide React | TBD | Low |
| Build Tool | Vite 6.2.0 | Astro (Vite-based) | Low |
| Charts | Recharts 3.6.0 | Recharts 3.6.0 | None |

### Backend

| Component | OmniPane | Bunny | Conflict Level |
|-----------|----------|-------|----------------|
| API | None (client-side) | GraphQL (Apollo Server) | High |
| Database | LocalStorage (planned) | Neo4j | High |
| Cache | N/A | Valkey | N/A |
| AI Service | Google Gemini (client) | Planned (backend) | Medium |

### Data Layer

| Component | OmniPane | Bunny | Conflict Level |
|-----------|----------|-------|----------------|
| Storage | LocalStorage JSON | Neo4j graph | High |
| Relationships | Object references | Graph relationships | High |
| Persistence | Browser-only | Server-backed | High |
| User State | Implicit (single user) | Multi-user required | High |

## Detailed Conflict Analysis

### 1. Frontend Framework Version Mismatch

**Conflict**: OmniPane uses React 19.2.3, Bunny uses React 18.3.1

**Impact**: 
- React 19 features may not be available in React 18
- Potential breaking changes in component APIs
- React Server Components support differs

**Resolution**:
- Upgrade Bunny frontend to React 19 (aligns with Lumina integration decision)
- OR adapt OmniPane components to React 18 (may lose some features)
- **Recommendation**: Upgrade to React 19 (already planned for Lumina)

### 2. State Management Architecture

**Conflict**: OmniPane uses LocalStorage + React state, Bunny uses GraphQL + Apollo Client

**Impact**:
- OmniPane components expect local state management
- Bunny architecture requires GraphQL queries/mutations
- Data synchronization patterns differ
- Real-time updates need GraphQL subscriptions

**Resolution**:
- Port OmniPane components to use Apollo Client hooks
- Create GraphQL queries/mutations for all operations:
  - Article CRUD operations
  - Board management
  - Tag filtering
  - Read/saved/archived state
- Use Apollo Client cache for local state management
- **Recommendation**: Gradual migration, start with queries, then mutations

### 3. Data Persistence Layer

**Conflict**: OmniPane stores data in LocalStorage (planned), Bunny uses Neo4j

**Impact**:
- Data structure differs (JSON objects vs graph nodes)
- Persistence scope differs (browser vs server)
- Query patterns differ (object access vs Cypher queries)
- Multi-user support requires server-side persistence

**Resolution**:
- Map OmniPane data structures to Neo4j schema
- Create GraphQL resolvers for all operations
- Design migration path from LocalStorage to Neo4j
- **Recommendation**: Design GraphQL schema first, then migrate components

### 4. Multi-User Support

**Conflict**: OmniPane is single-user, Bunny requires multi-user support

**Impact**:
- Article states (read, saved, archived) are user-specific
- Boards are user-specific
- Feed preferences are user-specific
- No user authentication in OmniPane

**Resolution**:
- Design schema with User nodes from the start
- User-specific relationships: `(:User)-[:HAS_READ]->(:Media)`, `(:User)-[:SAVED]->(:Media)`, etc.
- User-specific nodes: `(:User)-[:OWNS]->(:Board)`
- Add authentication layer
- **Recommendation**: Multi-user is a hard requirement, design accordingly

### 5. Source Type Coverage

**Conflict**: OmniPane supports more source types than Bunny

**Impact**:
- Missing platforms: RSS, Newsletter, Booru, Monitor
- Different conceptual models for some sources

**Resolution**:
- Extend Platform enum to include:
  - `RSS`
  - `NEWSLETTER`
  - `BOORU`
  - `MONITOR`
- Map OmniPane source types to Bunny platforms
- Handle platform-specific metadata in Handle/Media nodes
- **Recommendation**: Extend schema, maintain backward compatibility

### 6. Board/Collection Model

**Conflict**: OmniPane "Boards" vs Bunny "FeedGroups"

**Impact**:
- OmniPane Boards = user collections of articles (Pinterest-style)
- Bunny FeedGroups = source collections (creators/handles)
- Different purposes but similar concept

**Resolution**:
- Create separate `Board` node type for user collections
- Keep `FeedGroup` for source organization
- `Board` links to `Media` nodes, `FeedGroup` links to `Handle` nodes
- **Recommendation**: Separate concepts, both valuable

### 7. Tag System

**Conflict**: OmniPane uses free-form tags, Bunny doesn't have explicit tag system

**Impact**:
- Tags are core to OmniPane's filtering/organization
- Bunny schema doesn't have tag nodes or relationships
- Tags need to be queryable and filterable

**Resolution**:
- Create `(:Tag)` nodes in Neo4j
- Many-to-many: `(:Media)-[:TAGGED_WITH]->(:Tag)`
- Support tag extraction from various sources (booru tags, content analysis)
- GraphQL queries for tag filtering
- **Recommendation**: Tag system is essential, implement as nodes

### 8. AI Integration Pattern

**Conflict**: OmniPane uses Google Gemini client-side, Bunny plans backend AI agents

**Impact**:
- API key exposure in client-side code
- Generation happens on-demand in browser
- No caching or rate limiting in OmniPane approach
- Summaries stored in article state

**Resolution**:
- Move AI generation to backend GraphQL mutations
- Store summaries in Neo4j (Media node property or separate Summary node)
- Use backend AI agent architecture (LiteLLM)
- Cache AI responses in Valkey
- **Recommendation**: Backend-first approach for security and scalability

### 9. SauceNAO Integration

**Conflict**: OmniPane has mock SauceNAO, needs real implementation

**Impact**:
- Reverse image search is a core feature
- API key management needed
- Results should be stored in database

**Resolution**:
- Implement backend SauceNAO service
- Store results in Media node (sauce property)
- GraphQL mutation to trigger search
- Cache results to avoid duplicate searches
- **Recommendation**: Backend service with caching

### 10. Article State Management

**Conflict**: OmniPane manages read/saved/archived in local state, needs user-specific persistence

**Impact**:
- States are user-specific (different users have different read states)
- Need to persist across sessions
- Need efficient queries (all unread articles, all saved articles)

**Resolution**:
- Create relationships: `(:User)-[:READ]->(:Media)`, `(:User)-[:SAVED]->(:Media)`, `(:User)-[:ARCHIVED]->(:Media)`
- GraphQL queries filter by relationship existence
- Mutations create/delete relationships
- **Recommendation**: Use relationships, not properties, for user-specific state

### 11. Feed Aggregation Model

**Conflict**: OmniPane aggregates articles from multiple sources, Bunny focuses on Reddit

**Impact**:
- OmniPane expects unified feed from multiple source types
- Bunny's current schema is Reddit-focused
- Need unified query interface

**Resolution**:
- Extend Media/Post to support all source types
- Unified feed query that aggregates across platforms
- Source-specific metadata in platform-specific properties
- **Recommendation**: Unified Media type with platform-specific extensions

### 12. Layout Modes

**Conflict**: OmniPane has list/grid modes, Bunny currently has grid

**Impact**:
- UI component needs to support both modes
- Layout preference is user-specific

**Resolution**:
- Support both layouts in frontend components
- Store layout preference in user settings
- **Recommendation**: Frontend-only feature, no schema changes needed

## Integration Strategy

### Phase 1: Schema Design (No Code Changes)
1. Design GraphQL schema extensions:
   - Board type and operations
   - Tag type and operations
   - User-specific state relationships
   - Extended Platform enum
   - AI summary storage
2. Map OmniPane data models to Neo4j schema
3. Design queries/mutations for all operations
4. Design user authentication approach

### Phase 2: Backend Implementation
1. Extend Neo4j schema:
   - Add Tag nodes
   - Add Board nodes
   - Add User nodes
   - Add user-specific relationships
   - Extend Platform enum
2. Create GraphQL resolvers:
   - Article/Media queries with filters
   - Board CRUD operations
   - Tag operations
   - User state mutations (read/saved/archived)
   - AI summary generation
   - SauceNAO search
3. Implement backend services:
   - AI service (Gemini integration)
   - SauceNAO service
   - Tag extraction service

### Phase 3: Frontend Adaptation
1. Upgrade React to v19 (if not already done for Lumina)
2. Port OmniPane components to use Apollo Client:
   - ArticleList component
   - ArticleReader component
   - Sidebar component
   - InsightsView component
3. Replace LocalStorage with GraphQL mutations
4. Adapt feed queries to GraphQL
5. Implement user authentication

### Phase 4: Feature Enhancement
1. Implement real SauceNAO integration
2. Add RSS/newsletter/booru source support
3. Enhance with Bunny's advanced features (deduplication, etc.)
4. Add real-time updates via GraphQL subscriptions

## Risk Assessment

### High Risk
- **Data Migration**: Moving from LocalStorage to Neo4j requires careful mapping
- **State Management**: Refactoring components to use GraphQL is significant work
- **Multi-User Architecture**: Adding user system is a major architectural change
- **API Key Security**: Client-side AI API keys must be moved to backend

### Medium Risk
- **React Version**: Upgrade to React 19 may introduce breaking changes (mitigated by Lumina decision)
- **Tag System**: New tag system needs careful design for performance
- **Board Model**: Need to reconcile with existing FeedGroup concept
- **Source Type Extensions**: Adding new platforms requires schema and ingestion changes

### Low Risk
- **Styling**: Tailwind CSS is compatible
- **Icons**: Lucide React can be added easily
- **Charts**: Recharts already in both codebases
- **Layout Modes**: Frontend-only feature

## Dependencies to Add

### Frontend
```json
{
  "dependencies": {
    "lucide-react": "^0.562.0"
  }
}
```

### Backend (for AI and SauceNAO integration)
- Google Gemini API client (if using Gemini)
- OR LiteLLM (for multi-provider support)
- SauceNAO API client
- Tag extraction libraries (for content analysis)

## Recommendations

1. **Start with Schema**: Design GraphQL schema first, validate with stakeholders
2. **Incremental Migration**: Port components one at a time, don't big-bang
3. **Preserve UX**: Keep OmniPane's excellent UI/UX patterns
4. **Backend AI**: Move all AI generation to backend for security
5. **User System First**: Implement user authentication early
6. **Tag System**: Implement as nodes, not properties, for queryability
7. **Separate Boards and FeedGroups**: Both concepts are valuable, keep separate
8. **Test Thoroughly**: Data migration and multi-user requires extensive testing
9. **Document Mapping**: Document all data model mappings clearly

## Next Steps

1. Review GraphQL schema extensions with team
2. Design user authentication approach
3. Create prototype of article reading with GraphQL
4. Design migration strategy for any existing data
5. Plan React 19 upgrade (if not already done for Lumina)
6. Design backend AI integration architecture
7. Design tag extraction and management system
8. Design board management system

