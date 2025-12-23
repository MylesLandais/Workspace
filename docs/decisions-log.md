# Integration Decisions Log

This document tracks key decisions made during the Lumina Feed integration process.

## Decision: React Version Upgrade

**Date**: Integration Planning
**Status**: ✅ Accepted

**Decision**: Upgrade Bunny frontend from React 18 to React 19

**Rationale**: 
- Team encourages running latest versions
- Provides forward compatibility
- Enables use of React 19 features from Lumina codebase

**Implementation**: Update `frontend/package.json` to use React 19

---

## Decision: AI Integration Approach

**Date**: Integration Planning
**Status**: ✅ Accepted

**Decision**: AI features are future/beta, not core features. Architecture should leave room for "magic" moments where AI enhances UX. Next generation solution will hook up to agent dev toolkit.

**Rationale**:
- AI generation is not a core requirement
- Architecture should support extensibility for AI enhancements
- Future integration with agent dev toolkit planned

**Implementation**:
- Design schema with AI extension points
- Defer AI features to future development
- Keep architecture flexible for AI integration

---

## Decision: Multi-user Support

**Date**: Integration Planning
**Status**: ✅ Accepted

**Decision**: Multi-user support is required. Users need to track and configure views specific to their tastes.

**Rationale**:
- Users want personalized views and preferences
- Boards, entities, and preferences should be user-specific
- Design should support multi-tenancy from the start

**Implementation**:
- Include `userId: String!` in all user-specific nodes (SavedBoard, etc.)
- Design GraphQL queries/mutations with user context
- Implement user authentication/authorization
- Index on `userId` for efficient user-specific queries

---

## Decision: Relationship Types

**Date**: Integration Planning
**Status**: ✅ Accepted

**Decision**: Use free-form strings for relationship types, keep schema extensible for future normalization

**Rationale**:
- Team prefers type safety, but relationship types are beyond domain expertise
- Free-form strings provide flexibility
- Can normalize to enum in future if common patterns emerge

**Implementation**:
- Use `type: String!` on `RELATED_TO` relationship
- Index on type for query performance
- Consider enum migration if patterns emerge in usage

---

## Decision: Board/FeedGroup Organizational Model

**Date**: Integration Planning
**Status**: 🔄 Design Exploration Phase

**Decision**: Design exploration needed for organizational model. Traditional OPML folders are stale. Need to support entity/source selection as filters or channels/subscriptions.

**Rationale**:
- Boards (filter presets) and FeedGroups (source collections) both serve organizational purposes
- Need flexible model beyond traditional folder structure
- Should support modern use cases (channels, subscriptions, filters)

**Next Steps**:
- See [Board/FeedGroup Design Exploration](./lumina-board-feedgroup-design.md)
- Proposing unified "Channel" model
- Review and validate with team

**Recommendation**: Use Channel model that supports both source collections and filter presets

---

## Decision: Image Pool Storage

**Date**: Integration Planning
**Status**: ⏸️ Deferred

**Decision**: Defer decision on image pool storage structure

**Options**:
- Store as URL array on Creator node (simpler)
- Store as separate Media nodes with relationships (more flexible)

**Implementation**: Start with URL array, consider Media nodes if relationships needed

---

## Decision: Board Sharing

**Date**: Integration Planning
**Status**: ⏸️ Deferred

**Decision**: Defer board/channel sharing feature to future enhancement

**Rationale**: Focus on core functionality first, sharing can be added later if needed

---

## Notes

- All decisions should be revisited if requirements change
- Design explorations should be validated with team before implementation
- Deferred decisions should be tracked for future planning

