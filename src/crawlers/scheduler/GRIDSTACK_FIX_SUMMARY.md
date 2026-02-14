# Gridstack Dashboard Fix Summary

## Problem
The Gridstack dashboard was throwing `jinja2.exceptions.UndefinedError: 'catalog_items' is undefined` when accessing non-catalog views (list, stack).

## Root Cause
The Gridstack template widget content was hardcoded with Jinja2 template syntax embedded in JavaScript strings. When switching to list or stack views, the `catalog_items` variable was not passed to the template context, causing undefined variable errors.

## Solution
Modified all view modes in `imageboard_dashboard_gridstack.py` to ensure `catalog_items` is always calculated and passed to the template context, regardless of the current view mode.

### Changes Made

#### 1. Catalog View
- Added `display_df = df.sort_values(by='timestamp', ascending=False)` for consistent data
- Ensures `catalog_items` is always populated for widget content

#### 2. Stack View
- Added catalog_items calculation logic identical to catalog view
- Ensures widgets can display catalog data even in stack/thread view
- Maintains existing thread filtering functionality

#### 3. List View
- Added catalog_items calculation logic
- Uses original dataframe (not filtered) for catalog to ensure widget data completeness
- Maintains existing search and filter functionality

## Key Modifications

### File: imageboard_dashboard_gridstack.py

#### Lines 547-570 (Catalog View)
```python
display_df = df.sort_values(by='timestamp', ascending=False)

return render_template_string(
    HTML_TEMPLATE,
    catalog_items=catalog_items,  # Always included
    posts=display_df,
    # ...
)
```

#### Lines 562-615 (Stack View)
```python
# Added catalog_items calculation
threads_dict = {}
for _, row in df.iterrows():
    # ... catalog logic ...
catalog_items = list(threads_dict.values())
catalog_items.sort(key=lambda x: x['image_count'], reverse=True)

return render_template_string(
    HTML_TEMPLATE,
    catalog_items=catalog_items,  # Always included
    posts=display_df,
    # ...
)
```

#### Lines 617-675 (List View)
```python
# Added catalog_items calculation
threads_dict = {}
for _, row in df.iterrows():
    # ... catalog logic ...
catalog_items = list(threads_dict.values())
catalog_items.sort(key=lambda x: x['image_count'], reverse=True)

return render_template_string(
    HTML_TEMPLATE,
    catalog_items=catalog_items,  # Always included
    posts=display_df,
    # ...
)
```

## Verification

### Working Features
✅ All view modes (catalog, list, stack)
✅ Widget rendering (4 widgets: Stats, Catalog, Feed, Threads)
✅ Catalog items display (14 threads loaded)
✅ Image paths correctly populated
✅ Search functionality
✅ Tag filtering
✅ Board filtering
✅ Thread-specific views

### Test Results
```
GET /?view=catalog                    200 OK
GET /?view=list&q=irl                 200 OK
GET /?view=stack&thread=944476821   200 OK
GET /images/<filename>                200 OK
```

## Architecture Notes

### Why This Approach?
Gridstack dashboard uses a unique architecture:
1. Server-side Jinja2 rendering for data injection
2. Client-side Gridstack.js for widget management
3. Static widget content strings in JavaScript

This means widget content templates must have all required variables (`catalog_items`, `posts`) available at initial render time, even if they're not displayed in the current view.

### Data Flow
```
Flask Route
  ├─ Calculate catalog_items (all views)
  ├─ Filter/display_df (view-specific)
  └─ Render template with full context
       ├─ Jinja2 processes template
       └─ JavaScript widgetData objects contain rendered HTML
```

## Performance Impact
Minimal - catalog_items calculation is O(n) where n = total posts, which is already being iterated for other aggregations. The additional overhead is negligible.

## Future Improvements

### Potential Optimizations
1. Cache catalog_items calculation per session
2. Lazy-load widget content via AJAX
3. Separate widget templates into Jinja2 includes
4. Add widget state management API

### Alternative Approach
Instead of embedding Jinja2 in JavaScript strings, could use:
- Client-side API calls for widget data
- Template inheritance for widget definitions
- Web Workers for data processing

## Deployment Notes
After applying fixes:
```bash
docker stop imageboard_dashboard
docker compose -f docker-compose.crawler.yml up -d --force-recreate imageboard_dashboard
```

## Status
✅ Fixed - All view components working correctly
✅ Deployed - Gridstack dashboard operational
✅ Tested - Catalog, list, and stack views functional
