# Application Rewrite Requirements Analysis

## Critical Questions for Full Application Rewrite

This document identifies gaps and questions that must be answered before the team can execute a full application rewrite/refactor.

## 1. README Structure and Naming

### Current State
- **Root `README.md`**: Project overview, quick start, architecture
- **`docs/README.md`**: Documentation index
- **`docs/domains/feed/README.md`**: Feed domain overview
- **`docs/domains/subscriptions/README.md`**: Subscriptions domain overview
- **`app/backend/README.md`**: Backend setup
- **`app/frontend/README.md`**: Frontend setup

### Assessment
**Current naming is appropriate** - README.md is standard convention for directory overviews. However, we should clarify the purpose of each:

- Root README: **Project entry point** - what is this, how do I start?
- docs/README: **Documentation navigation** - where do I find what?
- Domain READMEs: **Domain overview** - what is this domain, key concepts, quick start
- App READMEs: **Component setup** - how do I develop this specific component?

### Recommendation
Keep current structure but add clear purpose statements to each README.

## 2. Requirements Clarity - What Actually Changed?

### Critical Gap: Implemented vs Planned vs Aspirational

The `requirements.md` document lists many features, but it's unclear:

1. **What's currently implemented?**
   - Reddit scraping: ✅ Implemented
   - GraphQL API: ✅ Implemented
   - Feed with cursor pagination: ✅ Implemented
   - Creator/Handle model: ✅ Implemented
   - Image ingestion and deduplication: ✅ Implemented
   - Bunny Feed components: ✅ Partially implemented

2. **What's planned for MVP?**
   - RSS feeds: ❓ Planned or future?
   - Email forwarding: ❓ Planned or future?
   - Browser extension: ❓ Planned or future?
   - AI features: ❓ Future (per decisions-log)
   - Multi-platform support (Twitter, Instagram, etc.): ❓ Planned or future?

3. **What's aspirational/vision?**
   - Reading analytics
   - Collaborative features
   - Content lifecycle management
   - Privacy-first architecture

### Questions That Must Be Answered

#### A. MVP Scope Definition
**Question**: What is the minimum viable product for the rewrite?

**Current understanding**:
- Reddit content ingestion ✅
- Feed display with filtering ✅
- Creator/Handle management ✅
- Saved boards/filters ✅

**Unclear**:
- Is RSS ingestion in MVP?
- Is multi-platform support in MVP?
- Are AI features in MVP? (decisions-log says future)
- What's the minimum feature set for launch?

#### B. Architecture Decisions
**Question**: What architectural decisions are final vs still being explored?

**From decisions-log**:
- React 19: ✅ Final
- Multi-user support: ✅ Final
- GraphQL over REST: ✅ Final
- Board/FeedGroup model: 🔄 Design Exploration
- Image pool storage: ⏸️ Deferred

**Critical**: Board/FeedGroup model is still in design exploration - this affects core data model!

#### C. Data Model Clarity
**Question**: What is the final data model we're building toward?

**Current state**:
- Post/Media nodes exist
- Creator/Handle nodes exist
- Subreddit nodes exist
- SavedBoard nodes exist (Bunny)

**Unclear**:
- How do Boards relate to FeedGroups?
- What's the relationship between Creator, Handle, and Source?
- Is there a unified "Item" type or separate Post/Media/Article types?

#### D. Integration Status
**Question**: What's the status of Bunny and Reader integration?

**From refactoring plan**:
- Bunny Feed components: ✅ Partially integrated
- Saved boards: ✅ Schema exists, needs verification
- Filtering: ⚠️ May have bugs

**Unclear**:
- Is Reader Reader integration planned for rewrite?
- What's the priority: complete Bunny integration first, or parallel work?

## 3. Specification Clarity for Rewrite

### What's Clear Enough
✅ **Technology Stack**: Neo4j, Valkey, GraphQL, Astro, React - well defined
✅ **Domain Boundaries**: Feed vs Subscriptions - clear separation
✅ **Core Data Model**: Nodes and relationships - well documented
✅ **Development Workflow**: Docker-based, mock data support - clear

### What Needs More Clarity

#### A. Feature Prioritization
**Issue**: `requirements.md` lists 12+ major features but doesn't prioritize.

**Needed**:
- Phase 1 (MVP): What must be done?
- Phase 2 (Post-MVP): What comes next?
- Phase 3+ (Future): What's aspirational?

#### B. API Contract Specification
**Issue**: GraphQL schema exists but may not match requirements.

**Needed**:
- Complete GraphQL schema specification
- Query/mutation contracts
- Error handling patterns
- Authentication/authorization model

#### C. Data Migration Strategy
**Issue**: If rewriting, how do we migrate existing data?

**Needed**:
- Current data model → Target data model mapping
- Migration scripts and procedures
- Rollback strategy
- Data validation after migration

#### D. Testing Requirements
**Issue**: What's the testing strategy for the rewrite?

**Needed**:
- Unit test coverage requirements
- Integration test requirements
- E2E test scenarios
- Performance benchmarks

## 4. What Changed from Old System?

### From REFACTORING_PLAN.md
The system is transitioning from:
- **Old**: "RepostRadar" branding, basic feed
- **New**: "Bunny" branding, filtered boards, creator-based organization

### Key Changes Identified
1. **Branding**: RepostRadar → Bunny
2. **Organization Model**: Simple feed → Boards with filters
3. **Entity Model**: Posts → Creator/Handle/Media model
4. **Filtering**: Basic → Person-based and source-based filtering

### Unclear Changes
- What other features are being added/removed?
- Are there breaking changes to the API?
- What's the migration path for existing users/data?

## 5. Recommendations for Rock-Solid Documentation

### Immediate Actions Needed

1. **Create MVP Specification Document**
   - Define Phase 1 (MVP) features explicitly
   - Mark each requirement as: MVP / Phase 2 / Future
   - Set success criteria for MVP

2. **Finalize Board/FeedGroup Model**
   - Complete design exploration
   - Document final data model
   - Update schema specifications

3. **Create Implementation Status Document**
   - What's implemented (with code references)
   - What's partially implemented (what works, what doesn't)
   - What's not implemented (needs to be built)

4. **Create Migration Guide**
   - Current state → Target state mapping
   - Data migration procedures
   - API migration guide (if breaking changes)

5. **Create Testing Specification**
   - Test coverage requirements
   - Critical test scenarios
   - Performance benchmarks

### Documentation Structure Improvements

Consider adding:
- `docs/mvp-specification.md` - Clear MVP scope
- `docs/implementation-status.md` - What's built vs planned
- `docs/migration-guide.md` - How to migrate from current to target
- `docs/testing-requirements.md` - Testing strategy and requirements

## Questions for User

Before the team can execute a full rewrite, we need answers to:

1. **MVP Scope**: What's the minimum feature set for the rewrite?
2. **Board Model**: What's the final Board/FeedGroup/Channel model? (currently in design exploration)
3. **Platform Support**: Is multi-platform (RSS, Twitter, etc.) in MVP or future?
4. **AI Features**: Confirmed future/not in MVP? (decisions-log says future)
5. **Reader Integration**: Is this part of the rewrite or separate?
6. **Data Migration**: Do we need to preserve existing data, or fresh start?
7. **Timeline**: What's the target timeline for MVP?
8. **Team Size**: How many developers will work on this?
9. **Breaking Changes**: Are we okay with breaking API changes?
10. **Testing Strategy**: What's the testing approach for the rewrite?

