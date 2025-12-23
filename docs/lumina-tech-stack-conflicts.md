# Lumina Tech Stack Conflicts and Integration Points

## Overview

This document identifies conflicts between Lumina Feed's tech stack and Bunny's existing architecture, and proposes integration strategies.

## Tech Stack Comparison

### Frontend

| Component | Lumina | Bunny | Conflict Level |
|-----------|--------|-------|----------------|
| Framework | React 19 + Vite | Astro + React 18 | Medium |
| State | React hooks + LocalStorage | GraphQL + Apollo Client | High |
| Styling | Tailwind CSS (CDN) | Tailwind CSS (installed) | Low |
| Icons | Lucide React | TBD | Low |
| Build Tool | Vite | Astro (Vite-based) | Low |

### Backend

| Component | Lumina | Bunny | Conflict Level |
|-----------|--------|-------|----------------|
| API | None (client-side) | GraphQL (Apollo Server) | High |
| Database | LocalStorage | Neo4j | High |
| Cache | N/A | Valkey | N/A |
| AI Service | Google Gemini (client) | Planned (backend) | Medium |

### Data Layer

| Component | Lumina | Bunny | Conflict Level |
|-----------|--------|-------|----------------|
| Storage | LocalStorage JSON | Neo4j graph | High |
| Relationships | Object references | Graph relationships | High |
| Persistence | Browser-only | Server-backed | High |

## Detailed Conflict Analysis

### 1. Frontend Framework Version Mismatch

**Conflict**: Lumina uses React 19, Bunny uses React 18

**Impact**: 
- React 19 features may not be available in React 18
- Potential breaking changes in component APIs
- React Server Components support differs

**Resolution**:
- Upgrade Bunny frontend to React 19 (low risk, mostly additive)
- OR adapt Lumina components to React 18 (may lose some features)
- **Recommendation**: Upgrade to React 19 for forward compatibility

### 2. State Management Architecture

**Conflict**: Lumina uses LocalStorage + React state, Bunny uses GraphQL + Apollo Client

**Impact**:
- Lumina components expect local state management
- Bunny architecture requires GraphQL queries/mutations
- Data synchronization patterns differ

**Resolution**:
- Port Lumina components to use Apollo Client hooks
- Create GraphQL queries/mutations for entity management
- Use Apollo Client cache for local state management
- **Recommendation**: Gradual migration, start with queries, then mutations

### 3. Data Persistence Layer

**Conflict**: Lumina stores data in LocalStorage, Bunny uses Neo4j

**Impact**:
- Data structure differs (JSON objects vs graph nodes)
- Persistence scope differs (browser vs server)
- Query patterns differ (object access vs Cypher queries)

**Resolution**:
- Map LocalStorage data structures to Neo4j schema
- Create GraphQL resolvers for entity management
- Design migration path from LocalStorage to Neo4j
- **Recommendation**: Design GraphQL schema first, then migrate components

### 4. AI Integration Pattern

**Conflict**: Lumina uses Google Gemini client-side, Bunny plans backend AI agents

**Impact**:
- API key exposure in client-side code
- Generation happens on-demand in browser
- No caching or rate limiting in Lumina approach

**Resolution**:
- Move AI generation to backend GraphQL mutations
- Use backend AI agent architecture (LiteLLM)
- Cache AI responses in Valkey
- **Recommendation**: Backend-first approach for security and scalability

### 5. Feed Generation Strategy

**Conflict**: Lumina generates feeds client-side, Bunny uses real ingestion pipeline

**Impact**:
- Lumina can generate on-demand mock content
- Bunny requires pre-ingested content in Neo4j
- Query patterns differ (API calls vs GraphQL queries)

**Resolution**:
- Use GraphQL feed query for real content
- Keep AI generation as enhancement/fallback
- Design hybrid approach: real content + AI enhancement
- **Recommendation**: Real content first, AI as enhancement layer

### 6. Source Mapping Model

**Conflict**: Lumina has dynamic `SourceLink[]`, Bunny has `Handle` nodes with relationships

**Impact**:
- Data structure similarity but implementation differs
- Lumina sources are part of identity object
- Bunny handles are separate nodes with relationships

**Resolution**:
- Map `SourceLink[]` to `Handle` nodes in Neo4j
- Use GraphQL fragments for handle queries
- Preserve dynamic source mapping in UI
- **Recommendation**: Adapt UI to work with Handle nodes, minimal changes

### 7. Board/Collection Concept

**Conflict**: Lumina "Boards" are filter presets, Bunny "FeedGroups" are source collections

**Impact**:
- Conceptual overlap but different purposes
- Boards = saved query parameters
- FeedGroups = source organization

**Resolution**:
- Extend FeedGroup concept to support saved filters
- OR create separate "SavedQuery" or "Board" entity
- Design unified collection concept
- **Recommendation**: Extend existing FeedGroup model to support filters

### 8. Theme System

**Conflict**: Lumina uses CSS variables, Bunny theme system unknown

**Impact**:
- Need to understand Bunny's theming approach
- CSS variables are compatible with most systems

**Resolution**:
- Analyze existing Bunny theme implementation
- Integrate Lumina theme variables
- Ensure compatibility
- **Recommendation**: CSS variables approach is clean, adopt if compatible

## Integration Strategy

### Phase 1: Schema Design (No Code Changes)
1. Design GraphQL schema extensions for entity management
2. Map Lumina data models to Neo4j schema
3. Design queries/mutations for all operations

### Phase 2: Backend Implementation
1. Create GraphQL resolvers for entity management
2. Implement Cypher queries for entity operations
3. Add source visibility/hidden flag support
4. Implement board/collection GraphQL types

### Phase 3: Frontend Adaptation
1. Upgrade React to v19 (if needed)
2. Port Lumina components to use Apollo Client
3. Replace LocalStorage with GraphQL mutations
4. Adapt feed display to GraphQL queries

### Phase 4: Feature Enhancement
1. Move AI generation to backend
2. Integrate with real ingestion pipeline
3. Enhance with Bunny's advanced features (deduplication, etc.)

## Risk Assessment

### High Risk
- **Data Migration**: Moving from LocalStorage to Neo4j requires careful mapping
- **State Management**: Refactoring components to use GraphQL is significant work
- **API Key Security**: Client-side AI API keys must be moved to backend

### Medium Risk
- **React Version**: Upgrade to React 19 may introduce breaking changes
- **Feed Generation**: Hybrid approach (real + AI) needs careful design
- **Board Concept**: Need to reconcile with existing FeedGroup model

### Low Risk
- **Styling**: Tailwind CSS is compatible
- **Icons**: Lucide React can be added easily
- **Theme System**: CSS variables are standard

## Dependencies to Add

### Frontend
```json
{
  "dependencies": {
    "lucide-react": "^0.562.0"
  }
}
```

### Backend (for AI integration)
- Google Gemini API client (if using Gemini)
- OR LiteLLM (for multi-provider support)

## Recommendations

1. **Start with Schema**: Design GraphQL schema first, validate with stakeholders
2. **Incremental Migration**: Port components one at a time, don't big-bang
3. **Preserve UX**: Keep Lumina's excellent UI/UX patterns
4. **Backend AI**: Move all AI generation to backend for security
5. **Test Thoroughly**: Data migration requires extensive testing
6. **Document Mapping**: Document all data model mappings clearly

## Next Steps

1. Review GraphQL schema extensions with team
2. Create prototype of entity management with GraphQL
3. Design migration strategy for LocalStorage data
4. Plan React 19 upgrade (if proceeding)
5. Design backend AI integration architecture

