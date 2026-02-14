# Gridstack Dashboard Refactoring Guide

## Overview
This document explains the best-practice refactoring of the imageboard dashboard to use Gridstack.js as a clean **layout layer**, following industry-standard patterns for integrating Gridstack into existing applications.

## Key Principles

### 1. Clear Separation of Concerns
```
┌─────────────────────────────────────────┐
│  Business Logic (Flask Backend)       │
│  ├─ Data processing                   │
│  ├─ Aggregations                     │
│  └─ API endpoints                    │
└─────────────────────────────────────────┘
              ↓ JSON serialization
┌─────────────────────────────────────────┐
│  Layout Layer (Gridstack.js)          │
│  ├─ Widget positioning                │
│  ├─ Drag/resize behavior             │
│  └─ Layout persistence              │
└─────────────────────────────────────────┘
              ↓ DOM manipulation
┌─────────────────────────────────────────┐
│  Presentation (Client-side Rendering)   │
│  ├─ Widget content renderers         │
│  └─ Interactive components            │
└─────────────────────────────────────────┘
```

### 2. What Gridstack Owns vs. What Your App Owns

**Gridstack Owns:**
- Panel position: `x, y` grid coordinates
- Panel size: `w, h` width and height
- Drag/resize behavior and event handling
- Breakpoint responsiveness
- Serialization via `save()` / `load()`

**Your App Owns:**
- Which widgets exist (IDs, types, titles)
- Data fetching and processing
- Widget rendering and internal controls
- Business logic and validation

## Implementation Pattern

### 1. Layout Model Definition

```typescript
// TypeScript/JavaScript layout model
type WidgetLayout = {
  id: string;           // Unique widget identifier
  x: number;           // Grid X coordinate (0-11 for 12-column grid)
  y: number;           // Grid Y coordinate
  w: number;           // Width in grid units
  h: number;           // Height in grid units
  title: string;       // Display title
};

// Default layout configuration
const defaultLayout: WidgetLayout[] = [
  { id: 'stats', x: 0, y: 0, w: 3, h: 4, title: '📊 Stats' },
  { id: 'catalog', x: 3, y: 0, w: 5, h: 8, title: '🔍 Catalog' },
  { id: 'feed', x: 8, y: 0, w: 4, h: 8, title: '📡 Feed' },
  { id: 'threads', x: 0, y: 4, w: 8, h: 10, title: '🧵 Threads' }
];
```

### 2. Grid Container Setup

```javascript
// Initialize Gridstack with proper configuration
function initGrid() {
  grid = GridStack.init({
    column: 12,              // 12-column grid system
    cellHeight: 100,          // Each grid cell is 100px high
    margin: 10,               // 10px margin between widgets
    animate: true,             // Smooth animations
    float: false,              // Don't overlap widgets
    disableOneColumnMode: false // Responsive behavior
  });
}
```

### 3. Widget Creation Pattern

```javascript
function createWidget(config) {
  const widgetEl = document.createElement('div');
  widgetEl.className = 'grid-stack-item';
  widgetEl.setAttribute('gs-id', config.id);
  
  // Position attributes (or use gs-auto-position)
  if (config.x !== undefined && config.y !== undefined) {
    widgetEl.setAttribute('gs-x', config.x);
    widgetEl.setAttribute('gs-y', config.y);
  } else {
    widgetEl.setAttribute('gs-auto-position', 'true');
  }
  
  // Size attributes
  widgetEl.setAttribute('gs-w', config.w);
  widgetEl.setAttribute('gs-h', config.h);
  
  // Widget structure: header + content area
  widgetEl.innerHTML = `
    <div class="grid-stack-item-content">
      <div class="widget-header">
        <span class="widget-title">${config.title}</span>
        <div class="widget-actions">
          <button class="widget-btn">🔄</button>
        </div>
      </div>
      <div id="widget-content-${config.id}"></div>
    </div>
  `;
  
  // Add to grid
  grid.addWidget(widgetEl);
  
  // Render content separately
  renderWidgetContent(config.id);
}
```

### 4. Content Rendering Separation

```javascript
// Business logic - data processing and rendering
const widgetContent = {
  stats: function() {
    return `
      <div class="stat-card">
        <span class="stat-value">${totalPosts}</span>
        <span class="stat-label">Posts</span>
      </div>
    `;
  },
  
  catalog: function() {
    return catalogItems.map(item => `
      <div class="catalog-item">
        <img src="/images/${item.preview_image}">
        <span>/${item.thread_id}</span>
      </div>
    `).join('');
  }
};

// Render widget content independently of layout
function renderWidgetContent(widgetId) {
  const contentEl = document.getElementById(`widget-content-${widgetId}`);
  if (contentEl && widgetContent[widgetId]) {
    contentEl.innerHTML = widgetContent[widgetId]();
  }
}
```

### 5. Layout Persistence

```javascript
// Auto-save on layout changes
grid.on('change', function(event, items) {
  if (!items) return;
  
  // Extract layout data from grid state
  const layout = items.map(item => ({
    id: item.id,
    x: item.x,
    y: item.y,
    w: item.w,
    h: item.h
  }));
  
  // Persist to localStorage
  localStorage.setItem('dashboardLayout', JSON.stringify(layout));
});

// Manual save
function saveLayout() {
  const layout = grid.save();
  localStorage.setItem('dashboardLayout', JSON.stringify(layout));
  alert('Layout saved!');
}

// Load saved or default layout
function loadLayout() {
  const saved = localStorage.getItem('dashboardLayout');
  const layout = saved ? JSON.parse(saved) : defaultLayout;
  
  layout.forEach(config => createWidget(config));
}
```

## Migration from Previous Implementation

### Before (Problematic Approach)
```javascript
// ❌ Jinja2 embedded in JavaScript strings
const widgetData = {
  stats: {
    content: `
      {% for item in catalog_items %}
      <div>{{ item.subject }}</div>
      {% endfor %}
    `
  }
};
```

**Problems:**
- Template processing happens at wrong layer
- Cannot update widget content independently
- Tight coupling between backend and frontend
- Hard to maintain and debug

### After (Best Practice)
```javascript
// ✅ Data injected as JSON, rendering on client
const catalogItemsData = {{ catalog_items | tojson }};

const widgetContent = {
  catalog: function() {
    return catalogItemsData.map(item => `
      <div>${item.subject}</div>
    `).join('');
  }
};
```

**Benefits:**
- Clear separation: Flask → JSON → JavaScript
- Independent widget content updates
- Easier to debug and test
- Better performance (less template processing)

## Gridstack Configuration Options

### Grid System
```javascript
{
  column: 12,              // Number of columns (standard: 12, 16, 24)
  cellHeight: 100,          // Height of each grid cell
  cellHeightThrottle: 50,    // For auto cell height
  margin: 10,               // Gap between widgets
  animate: true,             // Enable animations
  float: false,              // Allow overlapping (usually false)
  removable: '#trash',        // Selector for drop zone
  acceptWidgets: true,       // Allow external widgets
}
```

### Responsiveness
```javascript
{
  disableOneColumnMode: false,  // Mobile behavior
  minRow: 1,                   // Minimum grid height
  maxRow: 0,                   // Unlimited (or specific height)
}
```

### Interaction Control
```javascript
{
  disableDrag: false,        // Disable all dragging
  disableResize: false,       // Disable all resizing
  staticGrid: false,         // Entire grid static
  dragIn: '.new-widget',    // Allow dragging new widgets in
  dragOut: true,             // Allow dragging widgets out
}
```

## Widget Behavior Modifiers

### Locking Widgets
```html
<!-- Prevent dragging -->
<div class="grid-stack-item" gs-no-move="true">
  
<!-- Prevent resizing -->
<div class="grid-stack-item" gs-no-resize="true">
  
<!-- Completely locked -->
<div class="grid-stack-item" gs-locked="true">
```

### Auto-Positioning
```html
<!-- Let Gridstack choose position -->
<div class="grid-stack-item" gs-auto-position="true">
```

### Minimum/Maximum Sizes
```html
<!-- Size constraints -->
<div class="grid-stack-item" 
     gs-min-w="2" gs-min-h="3"
     gs-max-w="8" gs-max-h="10">
```

## Performance Optimization

### 1. Reduce DOM Re-renders
```javascript
// ❌ Bad: Re-render entire widget
function refreshWidget() {
  grid.removeWidget(widgetEl);
  createWidget(config);
}

// ✅ Good: Update only content
function refreshWidget(id) {
  const contentEl = document.getElementById(`widget-content-${id}`);
  contentEl.innerHTML = widgetContent[id]();
}
```

### 2. Debounce Layout Saves
```javascript
let saveTimeout;
grid.on('change', debounce(function(event, items) {
  saveLayout(items);
}, 500));

function debounce(func, wait) {
  let timeout;
  return function(...args) {
    clearTimeout(timeout);
    timeout = setTimeout(() => func.apply(this, args), wait);
  };
}
```

### 3. Lazy Load Widget Content
```javascript
function createWidget(config) {
  // Create widget skeleton first
  const widgetEl = document.createElement('div');
  widgetEl.innerHTML = `
    <div class="grid-stack-item-content">
      <div class="widget-header">...</div>
      <div class="widget-placeholder">Loading...</div>
    </div>
  `;
  grid.addWidget(widgetEl);
  
  // Load content asynchronously
  setTimeout(() => {
    renderWidgetContent(config.id);
  }, 0);
}
```

## Testing Strategy

### 1. Unit Tests
```javascript
// Test layout serialization
test('saveLayout returns valid structure', () => {
  const layout = grid.save();
  expect(layout).toBeInstanceOf(Array);
  layout.forEach(item => {
    expect(item).toHaveProperty('id');
    expect(item).toHaveProperty('x');
    expect(item).toHaveProperty('y');
    expect(item).toHaveProperty('w');
    expect(item).toHaveProperty('h');
  });
});

// Test widget content rendering
test('catalog widget renders items', () => {
  const html = widgetContent.catalog();
  expect(html).toContain('catalog-item');
  expect(html).toContain('/images/');
});
```

### 2. Integration Tests
```javascript
// Test widget creation
test('widget can be added to grid', () => {
  const config = { id: 'test', x: 0, y: 0, w: 2, h: 2, title: 'Test' };
  createWidget(config);
  
  const widgetEl = document.querySelector('[gs-id="test"]');
  expect(widgetEl).not.toBeNull();
});

// Test layout persistence
test('layout can be saved and restored', () => {
  const layout = grid.save();
  localStorage.setItem('testLayout', JSON.stringify(layout));
  
  grid.removeAll();
  const saved = localStorage.getItem('testLayout');
  grid.load(JSON.parse(saved));
  
  const restoredLayout = grid.save();
  expect(restoredLayout).toEqual(layout);
});
```

## Common Issues and Solutions

### Issue: Widget Content Not Updating
```javascript
// ❌ Problem
createWidget(config);
// Later...
createWidget(config); // Duplicate widget!

// ✅ Solution
function refreshWidget(id) {
  const contentEl = document.getElementById(`widget-content-${id}`);
  if (contentEl) {
    contentEl.innerHTML = widgetContent[id]();
  }
}
```

### Issue: Layout Not Persisting
```javascript
// ❌ Problem
grid.on('change', function(event, items) {
  localStorage.setItem('layout', items); // Wrong format!
});

// ✅ Solution
grid.on('change', function(event, items) {
  const layout = items.map(item => ({
    id: item.id,
    x: item.x,
    y: item.y,
    w: item.w,
    h: item.h
  }));
  localStorage.setItem('layout', JSON.stringify(layout));
});
```

### Issue: Widget Overlapping
```javascript
// ❌ Problem
GridStack.init({
  float: true,  // Allows overlap!
});

// ✅ Solution
GridStack.init({
  float: false,  // Prevents overlap
});
```

## Browser Compatibility

| Feature | Chrome | Firefox | Safari | Edge |
|----------|---------|----------|---------|-------|
| Basic Grid | ✅ | ✅ | ✅ | ✅ |
| Drag & Drop | ✅ | ✅ | ✅ | ✅ |
| Resize | ✅ | ✅ | ✅ | ✅ |
| Animations | ✅ | ✅ | ✅ | ✅ |
| Touch Events | ✅ | ✅ | ✅ | ✅ |

## Next.js Integration (Future)

If migrating to Next.js:

```tsx
// components/DashboardGrid.tsx
'use client';

import { useEffect, useRef } from 'react';
import { GridStack } from 'gridstack';
import 'gridstack/dist/gridstack.min.css';

export function DashboardGrid({ layout, onChange }) {
  const gridRef = useRef<HTMLDivElement>(null);
  const gsRef = useRef<GridStack | null>(null);

  useEffect(() => {
    if (!gridRef.current || gsRef.current) return;

    const grid = GridStack.init({
      column: 12,
      float: true,
      animate: true
    }, gridRef.current);
    
    gsRef.current = grid;

    grid.on('change', (_event, items) => {
      const updated = items.map((it) => ({
        id: it.id as string,
        x: it.x!,
        y: it.y!,
        w: it.w!,
        h: it.h!,
      }));
      onChange?.(updated);
    });

    return () => {
      grid.destroy(false);
      gsRef.current = null;
    };
  }, [onChange]);

  return (
    <div className="grid-stack" ref={gridRef}>
      {layout.map((w) => (
        <div
          key={w.id}
          className="grid-stack-item"
          data-gs-id={w.id}
          data-gs-x={w.x}
          data-gs-y={w.y}
          data-gs-width={w.w}
          data-gs-height={w.h}
        >
          <div className="grid-stack-item-content">
            {/* Render widget content */}
          </div>
        </div>
      ))}
    </div>
  );
}
```

## Summary

### Key Takeaways
1. **Separate layout from content** - Gridstack manages positioning, your app manages data
2. **Use JSON for data transfer** - Avoid embedding templates in JavaScript
3. **Persist layout separately** - Save grid state, not widget content
4. **Independent widget rendering** - Refresh content without recreating widgets
5. **Test in isolation** - Unit test layout logic separately from business logic

### Architecture Benefits
- ✅ Clear separation of concerns
- ✅ Easier maintenance and debugging
- ✅ Better performance (less re-rendering)
- ✅ Testable components
- ✅ Flexible for future enhancements

### Files in This Refactoring
- `imageboard_dashboard_v4.py` - Refactored dashboard following best practices
- `GRIDSTACK_REFACTORING_GUIDE.md` - This documentation
- Previous: `imageboard_dashboard_gridstack.py` - Old implementation (deprecated)

## References
- [Gridstack.js Official Documentation](https://gridstackjs.com/)
- [Gridstack React Integration](https://gridstackjs.com/demo/react.html)
- [Gridstack API Reference](https://gridstackjs.com/demo/mobile.html)
- [Best Practices for Dashboard Layouts](https://blog.openreplay.com/building-interactive-dashboards-with-gridstack-js/)
