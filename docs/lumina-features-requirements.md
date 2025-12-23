# Lumina Features, Requirements, and User Stories

This document catalogues features identified in Lumina Feed, their requirements, and user stories to guide development.

## Feature Catalog

### 1. Entity/Identity Management

**Description**: Comprehensive interface for managing creator/entity profiles with source mappings, relationships, and metadata.

**Priority**: High

**Requirements**:

1. **CRUD Operations**
   - Create new creator/entity profiles
   - Read/view creator details with all related data
   - Update creator information (name, bio, avatar, aliases, keywords)
   - Delete creator profiles (with cascade handling)

2. **Source Mapping**
   - Map multiple sources (Reddit, Instagram, Twitter, TikTok, YouTube, Web) to a single entity
   - Add/remove sources dynamically
   - Set source labels (e.g., "Main", "Spam", "Fan Page")
   - Toggle source visibility (hidden/visible in feeds)
   - Support multiple accounts per platform per entity

3. **Metadata Management**
   - Set aliases for entity name variations
   - Add context keywords for AI/content discovery
   - Manage avatar images
   - Optional image pools for entity visuals

4. **Relationship Management**
   - Define relationships between entities (e.g., "Best Friend", "Partner", "Co-star")
   - Add/remove relationships
   - View relationship network
   - Bidirectional relationship queries

5. **Search and Filter**
   - Search entities by name
   - Filter entities in list view
   - Quick access to recently edited entities

**User Stories**:

**US-1.1**: As a user, I want to create a new entity profile with basic information (name, bio, avatar), so that I can start tracking a creator's content across platforms.

**US-1.2**: As a user, I want to add multiple social media accounts to an entity, so that I can aggregate content from all their platforms in one feed.

**US-1.3**: As a user, I want to hide specific sources from my feed, so that I can filter out spam accounts or fan pages while keeping them in the system for reference.

**US-1.4**: As a user, I want to add aliases and context keywords to an entity, so that AI-powered features can better identify and categorize content related to that entity.

**US-1.5**: As a user, I want to define relationships between entities, so that I can discover related content and understand connections between creators.

**US-1.6**: As a user, I want to search for entities by name, so that I can quickly find and edit entity profiles.

**Acceptance Criteria**:
- Entity creation takes < 2 seconds
- Source addition/removal is instant (optimistic updates)
- All entity data persists across sessions
- Relationship network visualization works for up to 100 entities
- Search returns results in < 500ms

---

### 2. Saved Boards (Filter Presets)

**Description**: Save and quickly switch between filter configurations as named "Boards".

**Priority**: High

**Requirements**:

1. **Board Management**
   - Create boards from current filter state
   - Name boards with custom names
   - Delete boards
   - List all saved boards
   - Quick switch between boards

2. **Filter State**
   - Store person/entity filters
   - Store source/platform filters
   - Store search query
   - Preserve filter state when switching boards

3. **Board Persistence**
   - Persist boards across sessions
   - Support board updates
   - Optional: Board sharing (future)

**User Stories**:

**US-2.1**: As a user, I want to save my current filter configuration as a "Board", so that I can quickly return to this exact feed view later.

**US-2.2**: As a user, I want to switch between saved boards, so that I can alternate between different curated feeds (e.g., "Linux Rice", "Pop Culture", "Tech News").

**US-2.3**: As a user, I want to delete boards I no longer need, so that my board list stays organized and relevant.

**US-2.4**: As a user, I want boards to remember all my filter settings (persons, sources, search query), so that switching boards gives me the exact feed I configured.

**Acceptance Criteria**:
- Board creation takes < 1 second
- Board switching applies filters instantly
- Boards persist across browser sessions
- Board list displays up to 50 boards efficiently
- Board names are unique per user (or allow duplicates)

---

### 3. Advanced Filtering System

**Description**: Multi-dimensional filtering for feed content with visual feedback.

**Priority**: High

**Requirements**:

1. **Filter Types**
   - Person/Entity filtering (multi-select)
   - Source/Platform filtering (multi-select)
   - Free-text search query
   - Combine filters (AND logic)

2. **Filter UI**
   - Sidebar with filter options
   - Active filter chips in filter bar
   - Remove individual filters
   - Clear all filters option
   - Visual indicators for active filters

3. **Filter Behavior**
   - Filters apply immediately (no "Apply" button needed)
   - Feed refreshes on filter change
   - Preserve filter state in URL or local state
   - Support filter presets (boards)

**User Stories**:

**US-3.1**: As a user, I want to filter my feed by specific entities, so that I only see content from creators I'm interested in.

**US-3.2**: As a user, I want to filter by source/platform, so that I can focus on content from Reddit, Instagram, or other specific platforms.

**US-3.3**: As a user, I want to search for content by keywords, so that I can find posts about specific topics or themes.

**US-3.4**: As a user, I want to see which filters are currently active, so that I understand why I'm seeing certain content.

**US-3.5**: As a user, I want to remove individual filters quickly, so that I can refine my feed without starting over.

**Acceptance Criteria**:
- Filter application takes < 1 second
- Active filters are clearly visible
- Filter removal is instant
- Filters combine correctly (AND logic)
- Search query supports natural language

---

### 4. Visual Feed Display

**Description**: Masonry grid layout for displaying media content with rich metadata.

**Priority**: High

**Requirements**:

1. **Layout**
   - Responsive masonry/column layout
   - 1-4 columns based on viewport size
   - Break-inside-avoid for cards
   - Smooth scrolling

2. **Media Cards**
   - Image/video preview
   - Caption/title overlay
   - Source badge
   - Author information
   - Engagement metrics (likes, views)
   - Media type indicator (image, GIF, video)
   - Hover effects and interactions

3. **Media Handling**
   - Lazy loading images
   - Aspect ratio preservation
   - Multiple media types (image, video, GIF)
   - Fallback for missing media

4. **Interactions**
   - Click to view full-size
   - Hover to show metadata
   - Keyboard navigation (future)
   - Infinite scroll pagination

**User Stories**:

**US-4.1**: As a user, I want to see my feed in a visual grid layout, so that I can quickly scan and discover interesting content.

**US-4.2**: As a user, I want media cards to show source and author information, so that I know where content comes from.

**US-4.3**: As a user, I want to see engagement metrics (likes, views) on media cards, so that I can gauge content popularity.

**US-4.4**: As a user, I want media to load lazily, so that pages load quickly even with many items.

**US-4.5**: As a user, I want to click on media cards to view full-size content, so that I can see details and interact with the original post.

**Acceptance Criteria**:
- Feed loads initial 20 items in < 2 seconds
- Lazy loading triggers smoothly on scroll
- Media cards maintain aspect ratios
- Grid layout adapts to viewport size
- Hover effects are smooth and responsive

---

### 5. AI-Powered Content Generation (Optional Enhancement)

**Description**: Generate mock/example feed content using AI when real content is unavailable.

**Priority**: Low (Enhancement)

**Requirements**:

1. **Generation Strategy**
   - Use AI to generate contextual feed items
   - Fallback to fixtures when AI unavailable
   - Context-aware generation using entity profiles
   - Support for different media types

2. **Integration Points**
   - Backend AI service (not client-side)
   - Caching of generated content
   - Rate limiting and cost management
   - Quality control

**User Stories**:

**US-5.1**: As a system, I want to generate example feed content using AI, so that users can see the interface even when real content is not yet ingested.

**US-5.2**: As a user, I want AI-generated content to be contextually relevant to my filters, so that examples feel realistic and useful.

**Note**: This feature is lower priority as Bunny focuses on real content ingestion. Consider as enhancement or demo feature.

---

### 6. Theme System

**Description**: Multiple theme options for visual customization.

**Priority**: Medium

**Requirements**:

1. **Theme Options**
   - Default (Midnight) dark theme
   - Kanagawa (Dragon) warm dark theme
   - Additional themes (future)

2. **Theme Persistence**
   - Save theme preference
   - Apply theme on load
   - Smooth transitions between themes

3. **Theme Implementation**
   - CSS variables for colors
   - Root-level class switching
   - Consistent theming across all components

**User Stories**:

**US-6.1**: As a user, I want to switch between different themes, so that I can customize the visual appearance to my preference.

**US-6.2**: As a user, I want my theme preference to be saved, so that I don't have to change it every time I visit.

**Acceptance Criteria**:
- Theme switching is instant
- Theme persists across sessions
- All components respect theme colors
- Transitions are smooth

---

### 7. View Management

**Description**: Multiple views for different functions (feed, admin/entity management).

**Priority**: High

**Requirements**:

1. **Views**
   - Feed view (main content display)
   - Admin/Entity Manager view (entity management)
   - Smooth transitions between views

2. **Navigation**
   - Sidebar navigation
   - View state management
   - URL routing (future)

**User Stories**:

**US-7.1**: As a user, I want to switch between feed view and entity management view, so that I can manage my entities without losing my place in the feed.

**US-7.2**: As a user, I want clear navigation indicators showing which view I'm currently in, so that I always know where I am in the application.

**Acceptance Criteria**:
- View switching is instant
- View state is preserved when switching
- Navigation is clear and intuitive

---

## Cross-Cutting Requirements

### Performance

- Feed queries return results in < 2 seconds
- Entity management operations complete in < 1 second
- UI interactions feel instant (< 100ms)
- Infinite scroll pagination loads smoothly
- Lazy loading prevents performance degradation

### Data Consistency

- All entity data persists reliably
- Board configurations persist across sessions
- Filter state can be restored
- No data loss during operations

### User Experience

- Intuitive navigation and interactions
- Clear visual feedback for all actions
- Error messages are helpful and actionable
- Loading states are clear and informative
- Responsive design works on all screen sizes

### Accessibility

- Keyboard navigation support
- Screen reader compatibility
- High contrast mode support
- Focus indicators visible
- ARIA labels where appropriate

---

## Feature Dependencies

```
Entity Management (1)
  ├── Source Mapping (1.2)
  ├── Relationship Management (1.4)
  └── Metadata Management (1.3)

Saved Boards (2)
  └── Filtering System (3)

Filtering System (3)
  └── Feed Display (4)

Feed Display (4)
  ├── Media Handling
  └── Pagination

View Management (7)
  ├── Feed View (4)
  └── Entity Management View (1)

Theme System (6)
  └── All UI Components
```

---

## Implementation Phases

### Phase 1: Foundation (Core Features)
- Entity Management CRUD
- Basic filtering (persons, sources)
- Feed display with GraphQL
- View management

### Phase 2: Enhancement (User Experience)
- Saved Boards
- Advanced filtering UI
- Theme system
- Performance optimizations

### Phase 3: Advanced (Future)
- AI content generation (if needed)
- Relationship visualization
- Board sharing
- Advanced search

---

## Success Metrics

### User Engagement
- Daily active users
- Average entities created per user
- Average boards created per user
- Feed items viewed per session

### Performance
- Average feed load time
- Entity management operation time
- UI interaction response time
- Error rate

### Feature Adoption
- Percentage of users creating entities
- Percentage of users using saved boards
- Percentage of users applying filters
- Theme usage distribution

---

## Open Questions

1. **Multi-user Support**: Should boards and entities be user-specific or shared?
2. **Board Sharing**: Should users be able to share boards with others?
3. **Entity Verification**: Should there be a verification system for entity data?
4. **Relationship Types**: Should relationship types be standardized/enum or free-form?
5. **AI Integration**: Should AI generation be a core feature or demo-only?
6. **Image Pool**: Should image pools be stored as separate Media nodes or as URL arrays?

---

## Related Documentation

- [Lumina Analysis](./lumina-analysis.md) - Detailed codebase analysis
- [Component Interface Map](./lumina-component-interface-map.md) - Component specifications
- [Data Schema Expectations](./lumina-data-schema-expectations.md) - Schema requirements
- [Tech Stack Conflicts](./lumina-tech-stack-conflicts.md) - Integration challenges

