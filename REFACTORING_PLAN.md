# Bunny Design Refactoring Plan

## Completion Criteria

**Primary Goal**: Working feed that can be filtered and sorted, matching Bunny's design examples:
- **"Linux Rice" board**: Filter by sources (r/unixporn, r/hyprland, r/kde, r/gnome, r/UsabilityPorn, r/battlestations)
- **"Queens of Pop++" board**: Filter by entities/persons (Taylor Swift, Selena Gomez)

## Current State Analysis

### Backend Status
- ✅ Feed filtering by persons and sources is implemented in `app/backend/src/neo4j/queries/feed.ts`
- ✅ Saved boards GraphQL schema and resolvers exist (`getSavedBoards`, `createSavedBoard`, `updateSavedBoard`, `deleteSavedBoard`)
- ✅ GraphQL schema includes `FeedFilters` input type with `persons`, `sources`, `searchQuery`
- ✅ Neo4j constraints and indexes for SavedBoard nodes exist

### Frontend Status
- ✅ Index page (`/`) already uses `BunnyFeed` component with Bunny design
- ✅ Bunny sidebar component exists and matches design
- ✅ FilterBar component exists and matches design
- ✅ GraphQL queries (`FEED_WITH_FILTERS`, `GET_SAVED_BOARDS`) exist
- ✅ GraphQL mutations (`CREATE_SAVED_BOARD`, `DELETE_SAVED_BOARD`) exist
- ⚠️ Other pages still use old "RepostRadar" branding
- ⚠️ Need to verify feed filtering works end-to-end
- ⚠️ Need to verify saved boards work end-to-end

## Implementation Tasks

### Phase 1: Core Feed Functionality (Priority: Critical)

#### 1.1 Verify Feed Filtering Works
**Files to check/modify:**
- `app/frontend/src/components/bunny/BunnyFeed.tsx` - Verify filters are passed correctly to GraphQL
- `app/frontend/src/lib/graphql/queries.ts` - Verify `FEED_WITH_FILTERS` query structure
- `app/backend/src/neo4j/queries/feed.ts` - Verify filter logic handles persons and sources correctly

**Tasks:**
- [ ] Test filtering by persons (e.g., "Taylor Swift", "Selena Gomez")
- [ ] Test filtering by sources (e.g., "r/unixporn", "r/hyprland")
- [ ] Test combining person and source filters
- [ ] Test search query filtering
- [ ] Verify filter state updates feed correctly

#### 1.2 Verify Saved Boards Functionality
**Files to check/modify:**
- `app/frontend/src/components/bunny/BunnyFeed.tsx` - Verify board creation/loading works
- `app/frontend/src/components/bunny/Sidebar.tsx` - Verify board selection applies filters
- `app/backend/src/bunny/queries.ts` - Verify board CRUD operations

**Tasks:**
- [ ] Test creating a new board with current filters
- [ ] Test loading saved boards from GraphQL
- [ ] Test selecting a board applies its filters
- [ ] Test deleting a board
- [ ] Verify "Linux Rice" and "Queens of Pop++" demo boards work

#### 1.3 Fix Feed Filtering Backend Logic
**Issue**: Current filter logic in `feed.ts` may have issues with:
- Person filtering by slug vs displayName
- Source filtering by platform vs subreddit name
- Combining multiple filters correctly

**Files to modify:**
- `app/backend/src/neo4j/queries/feed.ts`

**Changes needed:**
- [ ] Fix person filtering to match by `displayName` or `name` (not just slug)
- [ ] Fix source filtering to match subreddit names (with/without "r/" prefix)
- [ ] Ensure filters combine with AND logic correctly
- [ ] Handle case where no filters are provided (show all)

### Phase 2: Branding and UI Consistency (Priority: High)

#### 2.1 Update Branding to "Bunny"
**Files to modify:**
- `app/frontend/src/components/layout/Sidebar.tsx` - Change "RepostRadar" to "Bunny"
- `app/frontend/src/pages/dashboard.astro` - Update title from "RepostRadar" to "Bunny"
- Any other files with "RepostRadar" branding

**Tasks:**
- [ ] Replace all "RepostRadar" references with "Bunny"
- [ ] Update page titles and meta descriptions
- [ ] Verify consistent branding across all pages

#### 2.2 Integrate Bunny Sidebar Across All Pages
**Decision**: Should all pages use Bunny sidebar, or only feed pages?

**Option A (Recommended)**: Use Bunny sidebar for all pages
- Update `MainLayout.astro` to use Bunny sidebar
- Map existing routes to Bunny sidebar navigation
- Remove or deprecate old `Sidebar.tsx` component

**Option B**: Keep Bunny sidebar only for feed pages
- Keep old sidebar for admin/management pages
- Use Bunny sidebar only for feed-related pages

**Files to modify:**
- `app/frontend/src/layouts/MainLayout.astro`
- `app/frontend/src/components/layout/Sidebar.tsx` (remove or update)

**Tasks:**
- [ ] Decide on sidebar approach (Option A or B)
- [ ] Integrate Bunny sidebar into main layout
- [ ] Update navigation to work with Bunny sidebar
- [ ] Test navigation between pages

### Phase 3: Feed Sorting and Enhancement (Priority: Medium)

#### 3.1 Add Feed Sorting
**Requirements:**
- Sort by date (newest first) - already implemented
- Sort by score/likes (highest first)
- Sort by relevance (if search query provided)

**Files to modify:**
- `app/frontend/src/components/bunny/FilterBar.tsx` - Add sort dropdown
- `app/frontend/src/lib/bunny/types.ts` - Add sort type
- `app/backend/src/neo4j/queries/feed.ts` - Add sort parameter

**Tasks:**
- [ ] Add sort dropdown to FilterBar
- [ ] Update GraphQL query to accept sort parameter
- [ ] Update backend to handle sorting
- [ ] Test sorting functionality

#### 3.2 Enhance Feed Display
**Files to check:**
- `app/frontend/src/components/bunny/FeedItem.tsx` - Verify displays correctly
- `app/frontend/src/components/bunny/BunnyFeed.tsx` - Verify masonry layout

**Tasks:**
- [ ] Verify masonry grid layout works correctly
- [ ] Verify media cards display all metadata
- [ ] Test responsive design (mobile, tablet, desktop)
- [ ] Verify lazy loading works

### Phase 4: Testing and Validation (Priority: High)

#### 4.1 Test Example Boards
**Test Cases:**
1. **"Linux Rice" board**:
   - Create board with sources: r/unixporn, r/hyprland, r/kde, r/gnome, r/UsabilityPorn, r/battlestations
   - Verify feed shows only posts from these subreddits
   - Verify board appears in sidebar "My Boards" section

2. **"Queens of Pop++" board**:
   - Create board with persons: "Taylor Swift", "Selena Gomez"
   - Verify feed shows only posts from these creators
   - Verify board appears in sidebar "My Boards" section

**Tasks:**
- [ ] Create "Linux Rice" board and verify filtering
- [ ] Create "Queens of Pop++" board and verify filtering
- [ ] Test switching between boards
- [ ] Verify board filters persist correctly

#### 4.2 End-to-End Testing
**Test Scenarios:**
- [ ] Create new board from current filters
- [ ] Select board and verify feed updates
- [ ] Modify filters and verify feed updates
- [ ] Save modified filters to existing board
- [ ] Delete board and verify it's removed
- [ ] Test with no filters (show all content)
- [ ] Test with multiple person filters
- [ ] Test with multiple source filters
- [ ] Test with search query
- [ ] Test combining all filter types

## File Changes Summary

### Files to Modify:

1. **Backend**:
   - `app/backend/src/neo4j/queries/feed.ts` - Fix filter logic for persons and sources

2. **Frontend - Core Components**:
   - `app/frontend/src/components/bunny/BunnyFeed.tsx` - Verify filter integration
   - `app/frontend/src/components/bunny/Sidebar.tsx` - Verify board functionality
   - `app/frontend/src/components/bunny/FilterBar.tsx` - Add sorting (optional)

3. **Frontend - Branding**:
   - `app/frontend/src/components/layout/Sidebar.tsx` - Update branding or remove
   - `app/frontend/src/pages/dashboard.astro` - Update title
   - `app/frontend/src/layouts/MainLayout.astro` - Integrate Bunny sidebar

4. **Frontend - Types**:
   - `app/frontend/src/lib/bunny/types.ts` - Add sort type if needed

### Files Already Correct:
- `app/frontend/src/pages/index.astro` - Already uses BunnyFeed
- `app/frontend/src/components/bunny/FeedItem.tsx` - Matches Bunny design
- `app/frontend/src/lib/graphql/queries.ts` - Queries exist
- `app/frontend/src/lib/graphql/mutations.ts` - Mutations exist
- `app/backend/src/schema/schema.ts` - Schema supports filters
- `app/backend/src/bunny/queries.ts` - Board CRUD exists

## Critical Issues to Address

### 1. Person Filter Matching
**Problem**: Backend filters by `slug` or `id`, but frontend may pass `displayName` (e.g., "Taylor Swift")
**Solution**: Update backend to match by `displayName`, `name`, or `slug`

### 2. Source Filter Matching
**Problem**: Backend filters by `platform` or `label`, but frontend may pass subreddit names (e.g., "r/unixporn")
**Solution**: Update backend to match subreddit names (with/without "r/" prefix)

### 3. Filter Combination Logic
**Problem**: Need to ensure AND logic works correctly when multiple filters are provided
**Solution**: Review and fix Cypher query logic in `feed.ts`

## Success Criteria

The refactoring is complete when:

1. ✅ Feed can be filtered by persons (e.g., "Taylor Swift", "Selena Gomez")
2. ✅ Feed can be filtered by sources (e.g., "r/unixporn", "r/hyprland")
3. ✅ Feed can be filtered by search query
4. ✅ Filters can be combined (AND logic)
5. ✅ Saved boards can be created with current filter state
6. ✅ Saved boards can be loaded and applied
7. ✅ Saved boards can be deleted
8. ✅ "Linux Rice" board example works (filters by sources)
9. ✅ "Queens of Pop++" board example works (filters by persons)
10. ✅ All "RepostRadar" branding replaced with "Bunny"
11. ✅ Bunny sidebar integrated across application
12. ✅ Feed displays correctly with masonry layout
13. ✅ All existing functionality preserved

## Next Steps

1. **Start with Phase 1.3** - Fix backend filter logic (critical for functionality)
2. **Then Phase 1.1** - Verify feed filtering works end-to-end
3. **Then Phase 1.2** - Verify saved boards work end-to-end
4. **Then Phase 2** - Update branding and UI consistency
5. **Finally Phase 4** - Test example boards and validate completion criteria





