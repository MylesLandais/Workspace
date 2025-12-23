# OmniPane Reader Codebase Analysis

## Overview

OmniPane Reader is a unified content consumption platform that aggregates articles and media from multiple sources (RSS, Twitter, newsletters, YouTube, Reddit, booru sites, and monitoring services) into a single reading interface with AI-assisted features.

## Architecture

### Tech Stack

- **Framework**: React 19.2.3 with TypeScript
- **Build Tool**: Vite 6.2.0
- **Styling**: Tailwind CSS (appears to be used but not in package.json)
- **Icons**: Lucide React 0.562.0
- **Charts**: Recharts 3.6.0
- **AI Integration**: Google GenAI SDK (@google/genai 1.34.0)
- **State Management**: React hooks (useState, useMemo) with local state
- **Data Persistence**: LocalStorage (implicit, not explicit in codebase)

### Project Structure

```
omnipane-reader/
├── App.tsx                 # Main application component with routing
├── index.tsx               # React entry point
├── types.ts                # TypeScript type definitions
├── metadata.json           # App metadata
├── components/
│   ├── Sidebar.tsx         # Navigation sidebar
│   ├── ArticleList.tsx     # Article list/grid view
│   ├── ArticleReader.tsx   # Article detail/reading view
│   ├── InsightsView.tsx    # Analytics/insights dashboard
│   ├── CompetitorCard.tsx  # (Deleted/not implemented)
│   └── RadarChart.tsx      # (Deleted/not implemented)
├── services/
│   ├── geminiService.ts    # Google Gemini AI integration
│   └── sauceNaoService.ts  # SauceNAO reverse image search (mock)
└── data/
    └── mockData.ts         # Mock data for feeds, articles, boards
```

## Core Features

### 1. Multi-Source Feed Aggregation

Supports multiple source types:
- **RSS**: Traditional RSS feeds
- **Twitter**: Twitter/X threads and posts
- **Newsletter**: Email newsletters
- **YouTube**: YouTube videos
- **Reddit**: Reddit posts
- **Booru**: Image board sites (Danbooru, etc.)
- **Monitor**: Content monitoring services (e.g., Kemono.party)

### 2. View Modes

The application supports multiple view modes:
- **Inbox**: Unread articles (default)
- **Read Later**: Saved articles
- **Archive**: Archived articles
- **Feed**: Filtered by specific source
- **Tag**: Filtered by topic/tag
- **Board**: Pinterest-style saved collections
- **Analytics**: Content insights dashboard

### 3. Article Organization

#### Boards (Collections)
- Pinterest-style collections
- Users can pin articles to boards
- Boards display article counts
- Articles can belong to multiple boards

#### Tags
- Auto-computed from article metadata
- Display tag counts
- Click to filter by tag
- Tags extracted from article metadata (e.g., booru tags, content tags)

#### Reading States
- **Read/Unread**: Tracks whether article has been viewed
- **Saved**: Bookmarked for later reading
- **Archived**: Moved to archive

### 4. Layout Modes

- **List View**: Traditional article list with previews
- **Grid View**: Masonry-style grid layout (optimized for image-heavy content)

### 5. AI-Assisted Features

#### Article Summarization
- Generates executive summaries using Google Gemini
- Extracts key takeaways (3 bullet points)
- On-demand generation (not automatic)
- Summaries stored with articles

#### Chat with Article
- Side-panel chat interface
- Context-aware questions about article content
- Uses article content as context for AI responses

#### SauceNAO Integration
- Reverse image search for identifying image sources
- Finds original artist/creator
- Displays similarity percentage
- Links to original sources (Pixiv, Twitter, Danbooru)

### 6. Analytics Dashboard

The InsightsView provides:
- **Key Metrics**: Total items, read ratio, saved count
- **Source Distribution**: Pie chart of content by source type
- **Topic Distribution**: Bar chart of top tags/topics
- Visual analytics using Recharts

### 7. Reading Experience

#### Article Reader Features
- Clean reading interface
- Source type indicators
- Tag display
- Image viewing with metadata (dimensions)
- External link to original source
- Text-to-speech placeholder (UI ready, not implemented)
- Share functionality placeholder

#### Article Actions
- Save/unsave for later
- Archive/unarchive
- Pin to board
- Mark as read (automatic on selection)

## Data Models

### FeedSource

```typescript
interface FeedSource {
  id: string;
  name: string;
  icon?: string;
  type: SourceType;
  unreadCount: number;
}
```

### Article

```typescript
interface Article {
  id: string;
  sourceId: string;
  title: string;
  author: string;
  content: string;           // HTML or text
  summary?: string;          // AI-generated summary
  publishedAt: string;       // ISO date string
  read: boolean;
  saved: boolean;
  archived: boolean;
  tags: string[];            // e.g., "rem_(re:zero)", "width:1080"
  type: SourceType;
  url: string;
  imageUrl?: string;
  imageWidth?: number;
  imageHeight?: number;
  sauce?: SauceResult;       // SauceNAO result
}
```

### Board

```typescript
interface Board {
  id: string;
  name: string;
  articleIds: string[];
}
```

### SauceResult

```typescript
interface SauceResult {
  similarity: number;
  sourceUrl: string;
  artistName: string;
  extUrl?: string;           // External URL (e.g., Danbooru)
}
```

## Component Architecture

### App.tsx (Main Container)

**Responsibilities**:
- View state management (inbox, later, archive, feed, tag, board, analytics)
- Article filtering logic
- Board management
- Article CRUD operations
- Mobile responsive sidebar handling

**Key State**:
- `activeView`: Current view mode
- `activeFeedId`: Selected feed filter
- `activeArticleId`: Selected article for reading
- `activeTag`: Selected tag filter
- `activeBoardId`: Selected board
- `layout`: List or grid layout mode
- `articles`: Article collection
- `boards`: Board collection

### Sidebar.tsx

**Features**:
- Main navigation (Inbox, Read Later, Archive, Insights)
- Board list with counts
- Feed source list with unread indicators
- Tag/topic list with counts
- Settings entry point
- Responsive mobile overlay

### ArticleList.tsx

**Features**:
- List and grid layout modes
- Article previews with metadata
- Read/unread indicators
- Source type badges
- Tag display
- Saved bookmark indicator
- Click to select article
- Date formatting (relative time)

### ArticleReader.tsx

**Features**:
- Article content display
- Toolbar with actions (save, archive, pin to board, chat, TTS placeholder)
- AI summary generation
- Chat interface overlay
- SauceNAO search for images
- Source metadata display
- External link to original
- Mobile back button

### InsightsView.tsx

**Features**:
- Key metrics cards
- Source distribution pie chart
- Top topics bar chart
- Data aggregation from articles

## Services

### geminiService.ts

**Functions**:
- `generateArticleSummary(content, title)`: Generates AI summary and key takeaways
- `chatWithArticle(content, question)`: Answers questions about article content

**Implementation**:
- Uses Google GenAI SDK
- Structured JSON responses with schemas
- System instructions for role definition
- Error handling

### sauceNaoService.ts

**Functions**:
- `findSauce(imageUrl)`: Reverse image search

**Current State**: Mock implementation (returns simulated results after delay)

## User Interface Patterns

### Responsive Design
- Mobile-first approach
- Hamburger menu for mobile
- Full-screen article reader on mobile
- Side-by-side layout on desktop

### Visual Design
- Clean, modern interface
- Slate color palette (grays, indigo accents)
- Card-based layouts
- Smooth transitions and animations
- Lucide icons throughout

### Interaction Patterns
- Click to select/open
- Hover states for interactivity
- Loading states for async operations
- Optimistic UI updates (article state changes)

## Key Design Decisions

### 1. Client-Side Only Architecture
- No backend server
- All state in React
- Mock data for demonstration
- LocalStorage would be used for persistence (not implemented)

### 2. On-Demand AI Features
- AI summarization is user-triggered, not automatic
- Reduces API costs
- Gives users control over when to use AI features

### 3. Board-Based Organization
- Pinterest-style collections
- More flexible than folders
- Articles can belong to multiple boards

### 4. Tag-Based Filtering
- Auto-computed from article metadata
- Enables content discovery
- Cross-source topic filtering

### 5. Unified Article Model
- Single Article type handles all source types
- Source-specific fields (e.g., booru tags) stored in tags array
- Flexible content field (HTML/text)

## Missing/Incomplete Features

1. **Data Persistence**: No actual LocalStorage implementation
2. **SauceNAO Integration**: Only mock implementation
3. **Text-to-Speech**: UI placeholder only
4. **Share Functionality**: Not implemented
5. **Settings Page**: Navigation exists but no implementation
6. **Board Creation**: UI exists but no create functionality
7. **Feed Management**: Add/remove feeds not implemented
8. **Real API Integration**: All data is mocked
9. **User Authentication**: No user system
10. **Real-Time Updates**: No live feed updates

## Strengths

1. **Clean UI/UX**: Excellent visual design and user experience
2. **Multi-Source Support**: Handles diverse content types well
3. **Flexible Organization**: Boards and tags provide flexible organization
4. **AI Integration**: Thoughtful integration of AI features
5. **Responsive Design**: Works well on mobile and desktop
6. **Type Safety**: Good TypeScript usage
7. **Component Structure**: Well-organized component architecture

## Integration Considerations

### Data Model Mapping

OmniPane's `Article` maps to Bunny's `Media`/`Post` nodes:
- `Article.id` → `Media.id`
- `Article.sourceId` → `Media.handle.id` or `Post.subreddit.name`
- `Article.type` → `Media.platform`
- `Article.tags` → Separate tag system needed in Neo4j
- `Article.saved` → User-specific state (needs User node)
- `Article.archived` → User-specific state (needs User node)
- `Article.read` → User-specific state (needs User node)

### Source Types

OmniPane source types map to Bunny platforms:
- `rss` → Not currently in Bunny schema (needs addition)
- `twitter` → `TWITTER` platform
- `newsletter` → Not in Bunny schema (needs addition)
- `youtube` → `YOUTUBE` platform
- `reddit` → `REDDIT` platform
- `booru` → Not in Bunny schema (needs addition)
- `monitor` → Not in Bunny schema (could map to existing Handle)

### Boards

Boards are user-specific collections of articles. In Bunny schema:
- Could extend existing `FeedGroup` concept
- Or create new `Board` node type
- User-specific (requires User node)
- Many-to-many relationship: `(:User)-[:OWNS]->(:Board)-[:CONTAINS]->(:Media)`

### Tags

OmniPane uses free-form tags. In Neo4j:
- Could create `(:Tag)` nodes
- Many-to-many: `(:Media)-[:TAGGED_WITH]->(:Tag)`
- Or store as array property (less queryable)

## Next Steps for Integration

1. **Schema Extensions**: Add missing source types, tag system, board system
2. **User System**: Implement user authentication and user-specific state
3. **GraphQL Schema**: Extend schema for boards, tags, article states
4. **Component Porting**: Port components to use GraphQL instead of local state
5. **AI Service Migration**: Move AI features to backend
6. **SauceNAO Integration**: Implement real SauceNAO API integration
7. **Real Feed Integration**: Connect to actual feed sources

