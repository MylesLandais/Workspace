#!/usr/bin/env python3
"""FastAPI server for analytics dashboard."""
import uvicorn
from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="Analytics Dashboard")

# Mount static files
CACHE_DIR = Path("/home/jovyan/workspaces/cache/imageboard")
app.mount("/static/images", StaticFiles(directory=str(CACHE_DIR / "shared_images")), name="images")

@app.get("/", response_class=HTMLResponse)
async def get_analytics():
    """Serve analytics dashboard."""
    analytics_path = Path("/home/jovyan/workspaces/analytics.html")
    return HTMLResponse(content=analytics_path.read_text(encoding='utf-8'))

@app.get("/analytics.html", response_class=HTMLResponse)
async def get_analytics_file():
    """Serve analytics dashboard."""
    analytics_path = Path("/home/jovyan/workspaces/analytics.html")
    return HTMLResponse(content=analytics_path.read_text(encoding='utf-8'))

if __name__ == "__main__":
    print("=" * 70)
    print("Analytics Dashboard Server")
    print("=" * 70)
    print("Serving at: http://0.0.0.0:8890")
    print("Press Ctrl+C to stop")
    print("=" * 70)
    
    uvicorn.run(app, host="0.0.0.0", port=8890)
