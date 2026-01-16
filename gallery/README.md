# Gallery Interface

Custom gallery interface for viewing catalogues and offline cached HTML with custom styling and components.

## Features

### Catalogue Browser
- **Multi-source support**: Browse by subreddit, channel, or other sources
- **Grid/List views**: Toggle between visual layouts
- **Sorting options**: New, Top, Controversial
- **Pagination**: Easy navigation through large catalogues
- **Real-time search**: Find posts by title or content

### HTML Viewer
- **Cached HTML viewer**: View offline cached pages
- **Custom styling**: Inject custom CSS into cached pages
- **IFrame isolation**: Safe viewing of cached content
- **Overlay indicators**: Visual indication of cached content

### Filtering & Controls
- **NSFW filter**: Toggle explicit content
- **Cached-only filter**: Show only cached items
- **Source filtering**: Browse by specific sources
- **Responsive design**: Works on mobile and desktop

## Architecture

```
gallery/
├── api/
│   └── main.py              # FastAPI server
├── frontend/
│   ├── components/
│   │   └── gallery.py       # Python gallery components
│   ├── scripts/
│   │   └── main.js         # Frontend JavaScript
│   └── styles/
│       └── main.css         # Custom styling
├── templates/
│   └── index.html          # Main HTML template
└── setup.py               # Installation script
```

## Quick Start

### 1. Install Dependencies

```bash
cd gallery
python setup.py
```

### 2. Start the Server

```bash
cd api
python main.py
```

### 3. Open in Browser

Navigate to: http://localhost:8001

## Usage

### Browsing Catalogues

1. Select a source from the sidebar
2. Choose sort order (New, Top, Controversial)
3. Browse through pages
4. Click any item to view

### Viewing Cached HTML

- Click on any item with "✓ Cached" badge
- Opens in modal viewer with iframe
- Custom styling automatically applied

### Searching

1. Enter search query in search box
2. Press Enter or click Search button
3. Results displayed in current view mode

### Filtering

- **NSFW**: Toggle to show/hide explicit content
- **Cached Only**: Toggle to show only cached items

## API Endpoints

### `GET /api/catalogue/{source}`
Get catalogue entries from source.

Parameters:
- `limit`: Number of items (default: 50, max: 200)
- `offset`: Pagination offset (default: 0)
- `sort`: Sort order (new, top, controversial)

Returns:
```json
{
  "source": "python",
  "entries": [...],
  "count": 50
}
```

### `GET /api/sources`
Get available sources.

Returns:
```json
{
  "sources": [
    {"name": "python", "count": 1234},
    {"name": "programming", "count": 987}
  ]
}
```

### `GET /api/search`
Search posts by title or content.

Parameters:
- `query`: Search query
- `limit`: Number of results (default: 50, max: 200)

Returns:
```json
{
  "query": "test",
  "results": [...],
  "count": 10
}
```

### `GET /api/post/{post_id}`
Get post metadata.

Returns:
```json
{
  "post": {
    "id": "abc123",
    "title": "Post Title",
    "url": "https://...",
    "score": 100,
    "num_comments": 50,
    "thumbnail": "/gallery/thumbnails/abc123.jpg",
    "cached": true
  }
}
```

### `GET /view/{post_id}`
View cached HTML for post.

Returns: HTML content

## Cache Management

### Cache Locations

- **HTML**: `~/.cache/gallery/html/`
- **Thumbnails**: `~/.cache/gallery/thumbnails/`

### Caching HTML

```python
from gallery.frontend.components.gallery import GalleryManager

manager = GalleryManager()
manager.cache_post_html("post_id", "<html>...</html>")
```

### Custom Styling

The HTML viewer automatically injects custom CSS:

```css
.gallery-overlay {
    position: fixed;
    top: 10px;
    right: 10px;
    background: rgba(0, 0, 0, 0.8);
    color: white;
    padding: 10px 15px;
    border-radius: 5px;
    z-index: 9999;
}
```

## Customization

### Themes

Edit `gallery/styles/main.css` to customize:

```css
:root {
    --primary-color: #6366f1;
    --background: #0f172a;
    --surface: #1e293b;
    /* ... more colors */
}
```

### Components

Extend `gallery/components/gallery.py`:

```python
class CustomViewer(HtmlViewer):
    def render_html_with_custom_style(self, post_id: str, html: str) -> str:
        custom_css = """
        <style>
            /* Your custom CSS */
        </style>
        """
        return custom_css + html
```

## Integration with Existing Code

### Using Gallery Manager

```python
from gallery.frontend.components.gallery import GalleryManager

manager = GalleryManager()

# Cache HTML
manager.cache_post_html(post_id, html_content)

# Get stats
stats = manager.get_stats()
print(f"Cached pages: {stats['cached_pages']}")
```

### Adding Items to Catalogue

```python
from feed.repositories.cached_post_repository import CachedPostRepository

repo = CachedPostRepository()
await repo.save_post(post_data)
```

## Performance

- **Caching**: Redis cache for fast data access
- **Lazy Loading**: Thumbnails load on scroll
- **Pagination**: Limit items per page
- **Optimized Queries**: Neo4j indexed queries

## Troubleshooting

### Port Already in Use

Change port in `api/main.py`:
```python
uvicorn.run(app, host="0.0.0.0", port=8002)  # Change port
```

### Cache Issues

Clear cache:
```bash
rm -rf ~/.cache/gallery/
```

### Thumbnails Not Showing

Generate thumbnails:
```python
from gallery.frontend.components.gallery import GalleryManager

manager = GalleryManager()
manager.generate_thumbnail(post_id, image_url)
```

## Future Enhancements

- [ ] Batch cache management
- [ ] Advanced search filters
- [ ] Collection management
- [ ] Export catalogues
- [ ] Image gallery mode
- [ ] Video player integration
- [ ] Dark/light theme toggle
- [ ] Keyboard shortcuts

## Dependencies

- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `aiofiles` - Async file operations
- `requests` - HTTP client
- `Pillow` - Image processing
- `neo4j` - Graph database
- `redis` - Caching

## License

ISC
