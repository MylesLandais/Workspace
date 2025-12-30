# Reader Integration - Decisions Needed

This document highlights key conflicts and decisions that need to be resolved before proceeding with Reader integration. Please review and provide guidance on each item.

## Critical Decisions

### 1. Platform Enum Extensions

**Conflict**: Reader supports source types not in Bunny's Platform enum.

**Current Platform Enum**:
- REDDIT
- YOUTUBE
- TWITTER
- INSTAGRAM
- TIKTOK
- VSCO

**Reader Additional Types Needed**:
- RSS
- NEWSLETTER
- BOORU
- MONITOR

**Questions**:
1. Should we extend the Platform enum to include these new types?
2. How should we handle RSS feeds? (They don't map to a specific "handle" concept)
3. How should we handle newsletters? (Email-based sources)
4. How should we handle booru sites? (Image board sites like Danbooru)
5. How should we handle monitor services? (Kemono.party, etc.)

**Recommendation**: Extend Platform enum to include all types. Create Source/Handle nodes for each type, with type-specific metadata stored as properties.

---

### 2. User System Architecture

**Conflict**: Reader is single-user, Bunny needs multi-user support.

**Questions**:
1. What authentication system should we use? (OAuth, JWT, session-based?)
2. Should users be able to share boards/articles? (Currently single-user)
3. How should we handle user preferences? (Layout mode, etc.)
4. Should there be admin users with special permissions?

**Recommendation**: 
- Implement JWT-based authentication
- Keep boards/articles user-specific initially (can add sharing later)
- Store preferences in User node properties
- No admin users initially (can add later if needed)

---

### 3. Article vs Media vs Post Naming

**Conflict**: Reader uses "Article", Bunny uses "Media" and "Post".

**Questions**:
1. Should we unify to a single type name? (Article, Media, or Content?)
2. Should we keep separate types with different purposes?
3. How should we handle Reddit posts vs RSS articles vs other content?

**Recommendation**: 
- Use "Media" as the unified type (already in Bunny schema)
- Extend Media node with article-specific properties (content, summary, etc.)
- Handle type differences via properties rather than separate node types

---

### 4. Board vs FeedGroup Concept

**Conflict**: Reader "Boards" are user collections of articles, Bunny "FeedGroups" are source collections.

**Questions**:
1. Should we keep both concepts separate?
2. Should we unify them into a single concept?
3. Can a FeedGroup contain Boards, or vice versa?

**Current Understanding**:
- **FeedGroup**: Collection of sources/creators (e.g., "Design Sources", "Dev Sources")
- **Board**: User collection of articles (e.g., "UI Inspiration", "Research Topics")

**Recommendation**: Keep separate. They serve different purposes:
- FeedGroups organize sources for ingestion
- Boards organize articles for reading/organization

---

### 5. Tag System Implementation

**Conflict**: Reader uses tags extensively, Bunny doesn't have explicit tag system.

**Questions**:
1. Should tags be nodes or properties?
2. How should tags be extracted? (From article metadata, content analysis, user-created?)
3. Should tags be user-specific or global?
4. How should we handle special tag formats? (e.g., "width:1080", "rem_(re:zero)")

**Recommendation**:
- Tags as nodes (enables efficient querying and aggregation)
- Many-to-many relationship: `(:Media)-[:TAGGED_WITH]->(:Tag)`
- Tags are global (can be filtered per user in queries)
- Support special formats as-is (store as tag name)

---

### 6. User-Specific State (Read/Saved/Archived)

**Conflict**: Reader manages state in local storage, needs to be user-specific in multi-user system.

**Questions**:
1. Should we use relationships or properties for user state?
2. How should we handle performance? (Many relationships per user)
3. Should state be indexed for fast queries?

**Recommendation**:
- Use relationships: `(:User)-[:READ]->(:Media)`, `(:User)-[:SAVED]->(:Media)`, `(:User)-[:ARCHIVED]->(:Media)`
- Index relationships for performance
- Efficient queries using relationship existence checks

---

### 7. AI Integration Strategy

**Conflict**: Reader uses client-side AI, needs to be backend for security.

**Questions**:
1. Which AI provider should we use? (Google Gemini, OpenAI, multi-provider?)
2. Should we cache AI responses? (Summaries, chat responses)
3. Should AI features be opt-in or always available?
4. How should we handle API rate limits?

**Recommendation**:
- Use LiteLLM for multi-provider support (future flexibility)
- Cache summaries and responses in Valkey
- AI features are always available (no opt-in needed)
- Implement rate limiting and queuing for API calls

---

### 8. SauceNAO Integration

**Conflict**: Reader has mock SauceNAO, needs real implementation.

**Questions**:
1. Should SauceNAO results be stored in database?
2. How should we handle API rate limits?
3. Should we cache results to avoid duplicate searches?
4. Should this be a premium feature?

**Recommendation**:
- Store results in Media node (sauce property)
- Cache results to avoid duplicate searches
- Implement rate limiting
- Free feature initially (can monetize later if needed)

---

### 9. Content Model Unification

**Conflict**: Reader's Article model vs Bunny's Media/Post model.

**Questions**:
1. How should we map Article fields to Media properties?
2. Should we support HTML content or plain text?
3. How should we handle image metadata? (width, height, dimensions)
4. How should we handle source attribution? (author, source URL)

**Recommendation**:
- Map Article to Media node
- Store content as HTML string
- Store image metadata as properties (width, height)
- Store author as User node relationship or property
- Store source via BELONGS_TO relationship

---

### 10. React Version

**Conflict**: Reader uses React 19, Bunny uses React 18.

**Status**: Already decided for Bunny integration - upgrade to React 19.

**Action**: Proceed with React 19 upgrade (already in progress for Bunny).

---

## Medium-Priority Decisions

### 11. Analytics Data Storage

**Question**: Should analytics be computed on-the-fly or pre-computed and stored?

**Recommendation**: Compute on-the-fly for MVP, add caching later if needed.

### 12. Pagination Strategy

**Question**: Cursor-based or offset-based pagination?

**Recommendation**: Cursor-based (already used in Bunny, better performance).

### 13. Real-Time Updates

**Question**: Should we use GraphQL subscriptions for real-time updates?

**Recommendation**: Phase 2 feature, not required for MVP.

### 14. Mobile App Support

**Question**: Should we plan for mobile app in addition to web?

**Recommendation**: Web-first, mobile app can be added later if needed.

---

## Implementation Priorities

### Phase 1: Core Features (MVP)
- [ ] Multi-source feed aggregation (basic)
- [ ] View modes (inbox, later, archive)
- [ ] Reading states (read, saved, archived)
- [ ] Basic article reading
- [ ] Source management (add/remove)

### Phase 2: Organization Features
- [ ] Boards (collections)
- [ ] Tags
- [ ] Tag-based filtering
- [ ] Board-based filtering

### Phase 3: Enhanced Features
- [ ] Layout modes (list/grid)
- [ ] Analytics dashboard
- [ ] Advanced filtering

### Phase 4: AI Features
- [ ] Article summarization
- [ ] Chat with article
- [ ] SauceNAO integration

---

## Next Steps

1. **Review this document** with the team
2. **Make decisions** on all critical items above
3. **Update documentation** with decisions
4. **Begin backend implementation** (Phase 1)
5. **Create ADR** for major architectural decisions

---

## Questions for User

Please provide guidance on:

1. **Platform extensions**: Should we add RSS, NEWSLETTER, BOORU, MONITOR to Platform enum?
2. **Authentication**: What authentication system should we use?
3. **Naming**: Should we use "Article", "Media", or "Content" as the unified type?
4. **Boards vs FeedGroups**: Confirm that we should keep them separate?
5. **Tags**: Confirm tags as nodes with TAGGED_WITH relationships?
6. **User state**: Confirm relationships for READ/SAVED/ARCHIVED?
7. **AI provider**: Which AI provider should we use? (Gemini, OpenAI, multi-provider?)
8. **SauceNAO**: Confirm backend implementation with caching?

Once these decisions are made, we can proceed with implementation.





