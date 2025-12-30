# Bunny Feed Analysis

## Executive Summary

This document analyzes the Bunny Feed application extracted from `bunny-feed.zip` to identify features, patterns, and integration points with the existing Bunny codebase. Bunny is a client-side React application that demonstrates a visual feed interface with entity management, saved boards, and AI-powered content generation.

## Application Overview

### Purpose
Bunny Feed is a visual media feed aggregator with smart AI filtering. It allows users to:
- Curate visual feeds filtered by persons/entities and sources
- Save filter presets as "Boards"
- Manage entity profiles with source mappings and relationships
- Generate feed content using Google Gemini AI or fetch from Reddit

### Architecture
- **Frontend**: Pure React 19 + TypeScript + Vite
- **State Management**: React hooks + LocalStorage
- **AI Integration**: Google Gemini AI (Gemini 3 Flash Preview)
- **Data Sources**: Reddit API (with fallback to mock data)
- **Styling**: Tailwind CSS with CSS variables for theming
- **Icons**: Lucide React

## Key Features Identified

### 1. Entity/Identity Management
**Component**: `EntityManager.tsx`

**Features**:
- Create, edit, and delete identity profiles
- Map multiple sources (Reddit, Instagram, Twitter, TikTok, YouTube, Web) to a single identity
- Source visibility toggling (hide/show specific sources)
- Context keywords for AI generation
- Relationship mapping between entities
- Image pools for identity visuals

**Data Model**:
```typescript
interface IdentityProfile {
  id: string;
  name: string;
  bio: string;
  avatarUrl: string;
  aliases: string[];
  sources: SourceLink[];  // Dynamic source mapping
  contextKeywords: string[];
  imagePool: string[];
  relationships: Relationship[];
}
```

### 2. Saved Boards (Filter Presets)
**Component**: `Sidebar.tsx`, `FilterBar.tsx`

**Features**:
- Save current filter state as a named "Board"
- Quick switch between boards
- Delete boards
- Persisted in LocalStorage

**Data Model**:
```typescript
interface SavedBoard {
  id: string;
  name: string;
  filters: FilterState;
  createdAt: number;
}
```

### 3. Filter System
**Components**: `Sidebar.tsx`, `FilterBar.tsx`

**Filter Types**:
- **Persons**: Multi-select list of tracked entities
- **Sources**: Multi-select list of platforms/sources
- **Search Query**: Free-text search input

**UI Patterns**:
- Active filter chips with remove buttons
- Toggle buttons in sidebar
- Visual indicators for active state
- Search with Enter key trigger

### 4. Visual Feed Display
**Component**: `FeedItem.tsx`, `App.tsx`

**Features**:
- Masonry/column layout (1-4 columns based on viewport)
- Media cards with hover effects
- Image overlay with caption and metadata
- Source badges
- Author information
- Like counts
- Media type indicators (image, GIF, short/video)
- Lazy loading images

**Layout**:
- Responsive column layout using CSS columns
- Breakpoints: 1 col (mobile), 2 cols (sm), 3 cols (lg), 4 cols (xl)
- Aspect ratio handling for different media types

### 5. AI-Powered Feed Generation
**Service**: `geminiService.ts`

**Features**:
- Generate mock feed items using Gemini AI
- Context-aware generation using entity profiles
- Fallback to fixtures when AI unavailable
- Reddit API integration for real content
- Content deduplication
- Shuffling for organic feel

**Generation Strategy**:
1. Fetch from Reddit API if filters match
2. Fallback to local fixtures if offline
3. Generate via Gemini if API key available
4. Use generic fallback if all fail

### 6. Theme System
**Components**: `Sidebar.tsx`, `App.tsx`

**Themes**:
- **Default (Midnight)**: Dark theme with indigo accents
- **Kanagawa (Dragon)**: Warm dark theme with green accents

**Implementation**:
- CSS variables for theme colors
- Theme persisted in LocalStorage
- Root-level class switching
- Smooth transitions

### 7. View Management
**Component**: `App.tsx`, `Sidebar.tsx`

**Views**:
- **Feed View**: Main feed display
- **Admin View**: Entity management interface

**Navigation**:
- Sidebar navigation
- View state management
- Mobile menu support

## Technical Implementation Details

### State Management
- React hooks (`useState`, `useEffect`, `useCallback`)
- LocalStorage for persistence
- Event-driven updates via custom events

### Data Persistence
- **Identity Graph**: Stored in `bunny_identity_graph` LocalStorage key
- **Saved Boards**: Stored in `bunny_saved_boards` LocalStorage key
- **Theme**: Stored in `bunny_theme` LocalStorage key

### API Integration
- Reddit JSON API (public endpoints)
- Google Gemini AI API
- No backend required (pure client-side)

### Styling Approach
- Tailwind CSS utility classes
- CSS variables for theming
- Custom animations and transitions
- Responsive design patterns

## Comparison with Bunny Architecture

### Similarities

1. **Entity/Creator Management**: Both systems manage entity profiles with multiple source mappings
2. **Feed Display**: Both use visual grid layouts for media content
3. **Source Mapping**: Both support multiple sources per entity
4. **Filter System**: Both have filtering capabilities

### Differences

| Aspect | Bunny | Bunny |
|--------|--------|-------|
| **Architecture** | Client-side only | Client-server (GraphQL) |
| **Data Storage** | LocalStorage | Neo4j graph database |
| **AI Integration** | Google Gemini (client-side) | Planned (backend agents) |
| **Feed Generation** | AI-generated or Reddit API | Real ingestion pipeline |
| **State Management** | React hooks | GraphQL queries |
| **Boards/Collections** | Saved filter presets | FeedGroups + Sources |
| **Relationships** | Simple object references | Graph relationships in Neo4j |
| **Theming** | CSS variables | Theme provider (to be analyzed) |
| **Media Handling** | Direct URLs | Storage system with deduplication |

### Integration Challenges

1. **Data Model Mismatch**:
   - Bunny uses flat identity profiles
   - Bunny uses graph relationships (Creator -> Handle -> Media)
   - Need to map Bunny's `IdentityProfile` to Bunny's `Creator`/`Handle` model

2. **State Management**:
   - Bunny uses LocalStorage + React state
   - Bunny uses GraphQL queries + Neo4j
   - Need GraphQL mutations for entity management

3. **Feed Generation**:
   - Bunny generates feeds client-side via AI or Reddit
   - Bunny uses real ingestion pipeline with Neo4j queries
   - Need to adapt feed queries to GraphQL

4. **Boards vs FeedGroups**:
   - Bunny boards are filter presets
   - Bunny FeedGroups are source collections
   - Need to reconcile concepts

5. **Source Visibility**:
   - Bunny has `hidden` flag on sources
   - Bunny may need similar feature for feed filtering

## Recommended Integration Approach

### Phase 1: Data Model Mapping
- Map `IdentityProfile` to `Creator` + `Handle` nodes
- Map `SavedBoard` filters to query parameters
- Design GraphQL schema for entity management

### Phase 2: Component Adaptation
- Port UI components to work with GraphQL
- Replace LocalStorage with GraphQL mutations/queries
- Adapt feed display to use GraphQL feed query

### Phase 3: Feature Enhancement
- Integrate AI feed generation into backend
- Add board/collection management
- Enhance source visibility controls

## Key Insights

1. **UI/UX Patterns**: Bunny demonstrates excellent UX patterns for entity management and feed display that should be preserved
2. **Source Mapping**: The dynamic source mapping system is more flexible than fixed social fields
3. **Filter Presets**: Saved boards provide valuable user workflow optimization
4. **AI Integration**: Client-side AI generation is interesting but should move to backend for consistency
5. **Theme System**: CSS variable approach is clean and maintainable

## Files Reference

- `App.tsx`: Main application component
- `components/EntityManager.tsx`: Entity management interface
- `components/Sidebar.tsx`: Navigation and filters
- `components/FilterBar.tsx`: Active filters display
- `components/FeedItem.tsx`: Media card component
- `services/geminiService.ts`: AI feed generation
- `services/contentGraph.ts`: Identity graph management
- `services/fixtures.ts`: Mock data and demo content
- `types.ts`: TypeScript type definitions





