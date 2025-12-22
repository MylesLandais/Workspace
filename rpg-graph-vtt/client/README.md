# Client - Frontend Application

This directory contains all frontend/client-side code for the RPG Graph VTT application.

## Structure

```
client/
├── src/              # Source files (reserved for future build pipeline)
│   └── README.md     # Build pipeline documentation
├── static/           # Static assets (served directly)
│   ├── css/          # Stylesheets
│   │   └── dice-roller.css
│   ├── js/           # JavaScript modules
│   │   ├── dice-visualizer.js    # 3D dice rendering (Three.js)
│   │   ├── dice-logic.js         # Dice notation parser
│   │   ├── dice-integration.js   # Character sheet integration
│   │   └── dice-chaos-tests.js   # Chaos engineering tests
│   ├── docs/         # Frontend documentation
│   │   └── dice-roller-spec.md   # Dice roller specification
│   ├── index.html    # Main character sheet page
│   └── dice-roller.html # Standalone dice roller demo
└── README.md
```

## Current Architecture

**MVP Approach**: All frontend code is in `static/` and served directly by FastAPI. No build step is required.

- **HTML**: Directly served from `static/`
- **CSS**: Organized in `static/css/`
- **JavaScript**: Organized in `static/js/` with modular files

## Serving

The FastAPI server in `../web/server.py` mounts this directory at `/static`, so files are accessible at:
- `http://localhost:8000/static/index.html`
- `http://localhost:8000/static/css/dice-roller.css`
- `http://localhost:8000/static/js/dice-visualizer.js`

## Development

### Standalone Testing

Open `static/dice-roller.html` directly in a browser for testing the dice roller component in isolation.

### Integration Testing

Start the FastAPI server:
```bash
cd ../web
python server.py
```

Then visit `http://localhost:8000` to see the integrated character sheet with dice rolling.

## Dependencies

- **Three.js** (r128) - Loaded from CDN for 3D rendering
- No build step required - vanilla JavaScript

## File Paths

All paths in HTML files are relative to the `static/` directory:
- `css/dice-roller.css` → `/static/css/dice-roller.css`
- `js/dice-visualizer.js` → `/static/js/dice-visualizer.js`

## Future Build Pipeline

The `src/` directory is reserved for future build pipeline integration. When ready:
1. Move source files from `static/` to `src/`
2. Configure build tool (webpack/vite/rollup) to output to `static/`
3. Update HTML files to reference built assets
