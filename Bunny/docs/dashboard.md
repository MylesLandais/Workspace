# Bunny Dashboard

Unified workspace dashboard with real-time collaboration, customizable widgets, and flexible layout management.

## Features

### Core Functionality

- **Grid Layout System**: Drag-and-drop widget arrangement with React Grid Layout
- **Multiple Tabs**: Organize widgets into separate workspaces
- **Canvas Mode**: Freehand drawing and whiteboarding
- **Layout Modes**: Manual, Master, Split, Grid presets for instant organization
- **Dark/Light Theme**: Matcha green tea theme with cozy vibes

### Collaboration

- **Real-time CRDT Sync**: Powered by Yjs for conflict-free collaboration
- **Cursor Tracking**: See other users' cursors in real-time
- **Room-based**: Join specific rooms via URL parameters
- **Chat Integration**: Built-in messaging (UI pending)

### Widget Types

- **Text**: Markdown-style notes and documentation
- **Reader**: Article reading with formatting
- **AI Chat**: Gemini AI integration for assistants
- **Chart**: Data visualization with Recharts
- **Feed**: RSS/GraphQL feed display (integration pending)
- **Masonry Wall**: Image wall from feed data (integration pending)
- **Search**: Search interface (backend pending)
- **Image**: Image display
- **Iframe**: Embed external content
- **Mermaid**: Diagram rendering
- **Tag Monitor**: AI-powered tag insights

## Architecture

```
app/dashboard/
  └─ page.tsx              # Main dashboard component

src/
  ├─ components/dashboard/
  │   ├─ WidgetFrame.tsx    # Widget container with drag handle
  │   ├─ DrawingCanvas.tsx  # Canvas for freehand drawing
  │   ├─ CollabCursors.tsx  # Real-time cursor display
  │   ├─ ContextMenu.tsx    # Right-click menus
  │   └─ widgets/           # Individual widget implementations
  │
  ├─ hooks/
  │   └─ useCollaboration.ts # Yjs collaboration logic
  │
  ├─ lib/
  │   ├─ types/dashboard.ts  # Type definitions
  │   ├─ themes/matcha.ts    # Theme configuration
  │   └─ services/
  │       ├─ geminiService.ts # AI integration
  │       └─ opmlService.ts   # Feed management

server/
  └─ yjs-server.cjs         # Collaboration WebSocket server
```

## Getting Started

### Prerequisites

- Node.js 18+
- Bun (package manager)

### Installation

1. Install dependencies:

```bash
cd app/client
bun install
```

2. Set up environment variables (optional):

```bash
# .env.local
NEXT_PUBLIC_GEMINI_API_KEY=your_gemini_key_here
```

### Development

#### Standard Mode (Single-user)

```bash
bun run dev
```

#### Collaboration Mode (Multi-user)

```bash
bun run dev:collab
```

This starts both:

- Next.js dev server on http://localhost:3000
- Yjs collaboration server on ws://localhost:3001

### Joining a Collaboration Room

Add `?room=roomname` to the URL:

```
http://localhost:3000/dashboard?room=team-workspace
```

## Usage

### Basic Operations

- **Add Widget**: Click the `+` button in the header
- **Add Tab**: Click `+` next to tab list
- **Add Canvas**: Click the pen tool icon
- **Delete Widget**: Click `X` in widget header or right-click > Delete
- **Rename**: Right-click on tab or widget > Rename
- **Switch Layout**: Use layout mode buttons (Free, Master, Split, Grid)

### Keyboard Shortcuts (Planned)

- `Cmd/Ctrl + N`: New widget
- `Cmd/Ctrl + T`: New tab
- `Cmd/Ctrl + W`: Close tab
- `Cmd/Ctrl + D`: Toggle dark mode

### Persistence

Dashboard state is automatically saved to `localStorage`:

- `bunny-dashboard-state-v1`: Tab and widget configuration
- `bunny-dashboard-tags-v1`: Tag definitions

## Integration Points

### Pending Integrations

1. **Feed Widget** -> GraphQL API
   - Connect to existing `GET_FEED` query
   - Filter by subreddit/source
   - Display in list or card format

2. **Masonry Wall Widget** -> Existing `MasonryGrid` component
   - Wrap existing component
   - Pass GraphQL data
   - Support lightbox integration

3. **Search Widget** -> Search API
   - Full-text search across content
   - Filter by type/source

4. **Tag System** -> Shared tag store
   - Sync with main app tagging
   - Cross-reference with Neo4j

## Theme Customization

The dashboard uses a matcha green tea theme merging emerald tones with industrial aesthetics:

```typescript
// Matcha colors
matcha-500: #22c55e  // Primary
matcha-600: #16a34a  // Hover
matcha-400: #4ade80  // Accent

// Industrial colors
industrial-900: #0f172a  // Dark surface
industrial-950: #020617  // Dark background
```

Customize in `tailwind.config.ts` and `src/lib/themes/matcha.ts`.

## Collaboration Server

The Yjs WebSocket server runs independently:

```bash
node server/yjs-server.cjs
```

**Configuration:**

- `COLLAB_PORT`: Server port (default: 3001)
- `COLLAB_HOST`: Bind host (default: localhost)

**Production Deployment:**

- Use PM2 or systemd for process management
- Consider Docker container for isolation
- Add authentication layer if needed

## Troubleshooting

### Collaboration not working

1. Check WebSocket server is running on port 3001
2. Verify firewall allows WebSocket connections
3. Check browser console for connection errors

### Widgets not loading

1. Verify all widget files exist in `src/components/dashboard/widgets/`
2. Check browser console for import errors
3. Ensure widget type is registered in `WidgetFrame.tsx`

### Canvas not saving

1. Check `canvasData` is being persisted in tab state
2. Verify `localStorage` has space available
3. Ensure canvas ref is properly initialized

## Contributing

When adding new widgets:

1. Create widget component in `src/components/dashboard/widgets/`
2. Add widget type to `WidgetType` enum in `dashboard.ts`
3. Register in `WidgetFrame.tsx` switch statement
4. Update this README with widget documentation

## Future Enhancements

- [ ] Keyboard shortcut system
- [ ] Widget marketplace/templates
- [ ] Board sharing/export
- [ ] Persistent server-side state (MySQL/Drizzle)
- [ ] Advanced collaboration features (voice, video)
- [ ] Mobile responsive layout
- [ ] Widget configuration UI
- [ ] Drag-to-add from sidebar
- [ ] Undo/redo for layout changes

## License

Part of the Bunny project.
