# Gridstack Refactoring - Quick Reference

## Architecture Comparison

### Before (imageboard_dashboard_gridstack.py) ❌
```javascript
// Jinja2 templates embedded in JavaScript strings
const widgetData = {
  catalog: {
    id: 'catalog-widget',
    x: 3, y: 0, w: 5, h: 8,
    title: '🔍 Catalog Explorer',
    content: `
      <div class="catalog-grid">
        {% for item in catalog_items[:12] %}
        <div class="catalog-item">
          <img src="/images/{{ item.preview_image }}">
        </div>
        {% endfor %}
      </div>
    `
  }
};
```

### After (imageboard_dashboard_v4.py) ✅
```javascript
// Data injected as JSON, rendering on client
const catalogItemsData = {{ catalog_items | tojson }};

const widgetContent = {
  catalog: function() {
    return `
      <div class="catalog-grid">
        ${catalogItemsData.slice(0, 12).map(item => `
          <div class="catalog-item">
            <img src="/images/${item.preview_image}">
          </div>
        `).join('')}
      </div>
    `;
  }
};
```

## Key Improvements

| Aspect | Before | After |
|--------|---------|--------|
| **Data Flow** | Jinja2 → JS strings | JSON → JS rendering |
| **Content Updates** | Full widget recreate | Independent content refresh |
| **Debugging** | Template parsing errors | Standard JS debugging |
| **Performance** | Template processing | Client-side rendering |
| **Separation** | Tight coupling | Clean architecture |
| **Maintainability** | Difficult | Easy |

## Quick Reference

### Gridstack Initialization
```javascript
grid = GridStack.init({
  column: 12,              // Grid columns
  cellHeight: 100,          // Row height (px)
  margin: 10,               // Widget spacing (px)
  animate: true,             // Enable animations
  float: false,              // No overlap
  disableOneColumnMode: false // Responsive on
});
```

### Widget Creation
```javascript
function createWidget(config) {
  const widgetEl = document.createElement('div');
  widgetEl.className = 'grid-stack-item';
  widgetEl.setAttribute('gs-id', config.id);
  widgetEl.setAttribute('gs-x', config.x);
  widgetEl.setAttribute('gs-y', config.y);
  widgetEl.setAttribute('gs-w', config.w);
  widgetEl.setAttribute('gs-h', config.h);
  
  widgetEl.innerHTML = `
    <div class="grid-stack-item-content">
      <div class="widget-header">
        <span class="widget-title">${config.title}</span>
        <button>🔄</button>
      </div>
      <div id="widget-content-${config.id}"></div>
    </div>
  `;
  
  grid.addWidget(widgetEl);
  renderWidgetContent(config.id);
}
```

### Layout Persistence
```javascript
// Auto-save on changes
grid.on('change', (event, items) => {
  const layout = items.map(item => ({
    id: item.id,
    x: item.x,
    y: item.y,
    w: item.w,
    h: item.h
  }));
  localStorage.setItem('dashboardLayout', JSON.stringify(layout));
});

// Manual save
function saveLayout() {
  const layout = grid.save();
  localStorage.setItem('dashboardLayout', JSON.stringify(layout));
}

// Load layout
function loadLayout() {
  const saved = localStorage.getItem('dashboardLayout');
  const layout = saved ? JSON.parse(saved) : defaultLayout;
  layout.forEach(config => createWidget(config));
}
```

### Widget Content Refresh
```javascript
// ✅ Good: Update only content
function refreshWidget(id) {
  const contentEl = document.getElementById(`widget-content-${id}`);
  if (contentEl && widgetContent[id]) {
    contentEl.innerHTML = widgetContent[id]();
  }
}

// ❌ Bad: Recreate entire widget
function refreshWidget(id) {
  grid.removeWidget(document.querySelector(`[gs-id="${id}"]`));
  const config = defaultLayout.find(w => w.id === id);
  createWidget(config);
}
```

## Common Tasks

### Add New Widget
```javascript
// 1. Add to default layout
defaultLayout.push({
  id: 'new-widget',
  x: 8, y: 8, w: 4, h: 4,
  title: '🆕 New Widget'
});

// 2. Add content render
widgetContent['new-widget'] = function() {
  return '<div>Widget content here</div>';
};

// 3. Create widget
createWidget({ id: 'new-widget', ... });
```

### Remove Widget
```javascript
// Find and remove widget
const widgetEl = document.querySelector('[gs-id="widget-id"]');
if (widgetEl) {
  grid.removeWidget(widgetEl);
}
```

### Lock Widget
```javascript
// Prevent dragging
const widgetEl = document.querySelector('[gs-id="widget-id"]');
widgetEl.setAttribute('gs-no-move', 'true');

// Prevent resizing
widgetEl.setAttribute('gs-no-resize', 'true');
```

### Resize Widget Programmatically
```javascript
const widgetEl = document.querySelector('[gs-id="widget-id"]');
grid.update(widgetEl, { w: 6, h: 8 });
```

## Performance Tips

### Reduce DOM Updates
```javascript
// ❌ Bad: Full page reload
function updateDashboard() {
  location.reload();
}

// ✅ Good: Update only changed widgets
function updateWidget(id) {
  refreshWidget(id);
}
```

### Batch Operations
```javascript
// Disable animations for batch operations
grid.batchUpdate(() => {
  widgets.forEach(w => {
    grid.update(w, { w: newWidth });
  });
});
```

### Virtual Scrolling (Advanced)
```javascript
// For large datasets, consider virtual rendering
const visibleWidgets = getVisibleWidgets();
visibleWidgets.forEach(w => {
  renderWidgetContent(w.id);
});
```

## Debugging

### Check Widget State
```javascript
const widgetEl = document.querySelector('[gs-id="stats"]');
console.log('Widget state:', {
  x: widgetEl.getAttribute('gs-x'),
  y: widgetEl.getAttribute('gs-y'),
  w: widgetEl.getAttribute('gs-w'),
  h: widgetEl.getAttribute('gs-h')
});

// Or use Gridstack API
const gridNode = grid.engine.nodes.find(n => n.id === 'stats');
console.log('Grid node:', gridNode);
```

### List All Widgets
```javascript
const layout = grid.save();
console.log('All widgets:', layout);
// Output: [{id, x, y, w, h}, ...]
```

### Monitor Events
```javascript
grid.on('added', (event, items) => {
  console.log('Widgets added:', items);
});

grid.on('removed', (event, items) => {
  console.log('Widgets removed:', items);
});

grid.on('resizestop', (event, el) => {
  console.log('Widget resized:', el.getAttribute('gs-id'));
});
```

## Grid System Math

### Calculate Widget Position
```
Grid width = 12 columns
Column width = (container width - margins) / 12

Widget X coordinate = 0-11 (left to right)
Widget Y coordinate = 0+ (top to bottom)
```

### Calculate Cell Height
```
Cell height = 100px (configured)
Widget height (h) = h * 100px
```

### Calculate Widget Size
```
Widget width (px) = w * (container width - margins) / 12
Widget height (px) = h * 100px
```

## CSS Grid vs Gridstack

### CSS Grid
```css
.dashboard {
  display: grid;
  grid-template-columns: repeat(12, 1fr);
  gap: 10px;
}
```
- Static layout
- No drag/resize
- Responsive via media queries
- Simpler, less features

### Gridstack
```javascript
GridStack.init({ column: 12, margin: 10 });
```
- Dynamic layout
- Drag/resize built-in
- Layout persistence
- More complex, more features

## Migration Checklist

- [x] Define layout model (WidgetLayout)
- [x] Create grid container component
- [x] Implement widget creation pattern
- [x] Separate content rendering
- [x] Add layout persistence
- [x] Remove old drag/resize code
- [x] Test all view modes
- [x] Verify responsive behavior
- [x] Add save/reset controls
- [x] Document architecture

## Troubleshooting

### Widget Not Showing
```javascript
// Check if widget was added to DOM
console.log(document.querySelector('[gs-id="my-widget"]'));

// Check if grid initialized
console.log(grid.engine.nodes);
```

### Layout Not Saving
```javascript
// Check localStorage
console.log(localStorage.getItem('dashboardLayout'));

// Check event listener
grid.on('change', (event, items) => {
  console.log('Layout changed:', items);
});
```

### Drag/Resize Not Working
```javascript
// Check if grid is initialized
console.log('Grid initialized:', grid !== null);

// Check widget attributes
const widget = document.querySelector('.grid-stack-item');
console.log('Widget classes:', widget.className);
```

## Resources

- [Official Gridstack Docs](https://gridstackjs.com/)
- [Gridstack Demo Gallery](https://gridstackjs.com/demo/)
- [Gridstack GitHub](https://github.com/gridstack/gridstack.js)
- [This Project](/home/warby/Workspace/jupyter/)

## Version History

- **v1** - Initial Gridstack integration (imageboard_dashboard_gridstack.py)
- **v2** - Fixed undefined variable errors
- **v3** - Layout layer refactoring attempt
- **v4** - Best practice implementation (imageboard_dashboard_v4.py) ✅

## Status

✅ **Production Ready**
- Clean architecture
- All views working
- Layout persistence
- Documentation complete
- Tested and verified
