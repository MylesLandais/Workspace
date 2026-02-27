# Imageboard Dashboard - Gridstack Integration

## Overview
The imageboard dashboard has been upgraded to use Gridstack.js for interactive, draggable widget layouts.

## Features

### Interactive Widgets
- **Overview Stats** - Shows total posts, moderated content, images, and active threads
- **Catalog Explorer** - Browse threads with preview images and tags
- **Live Feed** - Recent posts gallery with real-time updates
- **Thread Clusters** - Classic thread view with post hierarchies

### Gridstack Capabilities
- **Drag & Drop** - Reorganize widgets by dragging headers
- **Resize** - Expand or shrink widgets to fit your workflow
- **Layout Persistence** - Save and restore custom layouts using browser localStorage
- **Responsive** - Adapts to different screen sizes (12-column grid)

### Quick Actions
- Save Layout - Store current widget positions
- Reset Layout - Return to default arrangement
- Refresh Widget - Reload individual widget content

## Usage

### Accessing the Dashboard
```
http://localhost:5001
```

### Managing Widgets
1. **Move** - Click and drag widget headers to reposition
2. **Resize** - Drag widget borders to change dimensions
3. **Save** - Click "Save Layout" to persist arrangement
4. **Reset** - Click "Reset Layout" to restore defaults

### Widget Details

#### 📊 Overview Stats
- Total posts crawled
- Moderated/flagged content
- Total images in cache
- Active thread count
- Position: Top-left (3 columns wide, 4 rows high)

#### 🔍 Catalog Explorer
- Grid view of all threads
- Preview images for visual identification
- Intelligence tags (irl, feet, goon, etc.)
- Image counts and moderation status
- Position: Top-center (5 columns wide, 8 rows high)

#### 📡 Live Feed
- Gallery of recent posts
- Chronological display
- Quick access to full threads
- Position: Top-right (4 columns wide, 8 rows high)

#### 🧵 Thread Clusters
- Classic imageboard thread view
- OP posts with full images
- Reply posts with navigation
- Inline moderation flags
- Position: Middle-left (8 columns wide, 10 rows high)

## Technical Details

### Stack
- **Frontend**: Gridstack.js 7.5.1 + Bootstrap 5.3
- **Backend**: Flask (Python)
- **Data**: Pandas + Parquet
- **Storage**: Browser localStorage for layouts

### Grid Configuration
```javascript
{
  column: 12,
  cellHeight: 100,
  margin: 10,
  animate: true,
  disableOneColumnMode: false,
  float: false
}
```

### Widget IDs
- `stats-widget` - Overview statistics
- `catalog-widget` - Thread catalog
- `feed-widget` - Live post feed
- `threads-widget` - Thread clusters

## Customization

### Adding New Widgets
1. Add widget data to `widgetData` object:
```javascript
myWidget: {
  id: 'my-widget-id',
  x: 0, y: 0, w: 4, h: 6,
  title: '🔮 My Widget',
  content: '<div>Widget HTML here</div>'
}
```

2. Create widget in DOMContentLoaded:
```javascript
const widget = createWidget('myWidget', widgetData.myWidget);
grid.addWidget(widget);
```

### Styling Widgets
Modify `.grid-stack-item-content` CSS for global widget styling:
```css
.grid-stack-item-content {
  background: var(--card-bg);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 15px;
  /* ... */
}
```

### Custom Colors
Adjust CSS variables in `:root`:
```css
:root {
  --bg-dark: #0b0d14;
  --card-bg: #151921;
  --accent: #38bdf8;
  /* ... */
}
```

## Persistence

### Layout Storage
Layouts are automatically saved to localStorage on drag/resize:
```javascript
const layout = grid.save();
localStorage.setItem('dashboardLayout', JSON.stringify(layout));
```

### Manual Save
Click "Save Layout" button to force save current arrangement.

### Reset
Click "Reset Layout" to clear stored layout and reload defaults.

## Data Sources

### Parquet File
Location: `/datasets/parquet/imageboard_weekly_latest.parquet`
- Updated by imageboard_pipeline every 6 hours
- Contains posts, threads, images, moderation data

### Images
Location: `/cache/imageboard/shared_images/`
- Deduplicated image cache
- Served via `/images/<filename>` route

### Tags
Configured keywords:
- irl - Real-life content
- feet - Foot-related content
- goon - NSFW content markers
- cel - Celebrity content
- zoomers - Generation-specific content
- panties - Adult content markers

## API Routes

### Main Dashboard
```
GET /?view=catalog  # Catalog view (default)
GET /?view=list      # Live feed view
GET /?view=stack     # Thread clusters view
GET /?board=<b>     # Filter by board
GET /?q=<query>     # Search posts
```

### Image Serving
```
GET /images/<filename>  # Serve cached images
```

## Troubleshooting

### Layout Not Saving
- Check browser localStorage permissions
- Ensure no ad blocker interfering
- Check browser console for errors

### Widgets Not Draggable
- Verify Gridstack.js loaded (check browser console)
- Ensure no CSS conflicts
- Check browser compatibility (modern browsers only)

### Images Not Loading
- Verify image files exist in cache directory
- Check Flask image route is accessible
- Check file permissions

### Performance Issues
- Limit catalog to top 12 threads (modify `{% for item in catalog_items[:12] %}`)
- Reduce widget dimensions to decrease DOM elements
- Enable `animate: false` for faster dragging

## Future Enhancements

Potential additions:
- Real-time WebSocket updates for live feed
- Add/remove widgets dynamically
- Export layouts to JSON
- Widget templates marketplace
- Multi-dashboard support
- Widget state management
- API-based widget content loading

## Migration from Classic Dashboard

The classic dashboard (`imageboard_dashboard.py`) is preserved and can be used by:
1. Editing `docker-compose.crawler.yml` line 64
2. Change: `./imageboard_dashboard_gridstack.py:` to `./imageboard_dashboard.py`
3. Restart container

## License
Part of the Jupyter Imageboard Crawler project.
