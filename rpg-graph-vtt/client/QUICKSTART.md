# Quick Start - Viewing the Frontend

## Option 1: FastAPI Server (Recommended)

The FastAPI server serves the frontend and provides API integration.

### Start the Server

```bash
cd rpg-graph-vtt/web
python server.py
```

### Access URLs

- **Character Sheet**: http://localhost:8000
- **Dice Roller Demo**: http://localhost:8000/static/dice-roller.html
- **API Documentation**: http://localhost:8000/docs

### From Docker

```bash
docker exec -it jupyter bash
cd /home/jovyan/workspaces/rpg-graph-vtt/web
python server.py
```

## Option 2: Direct File Access (Quick Testing)

For quick testing of the dice roller component in isolation:

### Standalone Dice Roller

Simply open the HTML file directly in your browser:

```bash
# From project root
open rpg-graph-vtt/client/static/dice-roller.html
# Or
xdg-open rpg-graph-vtt/client/static/dice-roller.html  # Linux
```

**Note**: When opening directly, Three.js will load from CDN, but API calls won't work. Use this only for testing the dice animation component.

## No Build Step Required

This is vanilla HTML/CSS/JavaScript - no build tools needed!

- ✅ No Bun required
- ✅ No npm/yarn required  
- ✅ No webpack/vite required
- ✅ Just open and view!

## Development Workflow

1. **Edit files** in `client/static/`
2. **Refresh browser** (server auto-reloads on Python changes)
3. **Test dice roller** at http://localhost:8000/static/dice-roller.html
4. **Test character sheet** at http://localhost:8000

## Troubleshooting

### Port 8000 Already in Use

```bash
# Find what's using the port
lsof -i :8000

# Or use a different port
uvicorn server:app --host 0.0.0.0 --port 8001
```

### Three.js Not Loading

Check browser console for CDN errors. The dice roller requires Three.js from CDN:
```html
<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
```

### CORS Issues

If accessing from a different origin, the FastAPI server may need CORS middleware. Currently configured for same-origin requests.

