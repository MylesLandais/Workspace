"""FastAPI server for RPG Graph VTT character sheet frontend."""

import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

# Add project root to path
# Support both standalone and monorepo contexts
project_root = Path(__file__).parent.parent
monorepo_root = project_root.parent  # Go up one more level for monorepo

# Add both paths to support imports
for path in [project_root, monorepo_root]:
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from web.api.routes import api_router

app = FastAPI(title="RPG Graph VTT", version="0.1.0")

# Mount static files from client directory
client_static_dir = project_root / "client" / "static"
app.mount("/static", StaticFiles(directory=client_static_dir), name="static")

# Include API routes
app.include_router(api_router)


@app.get("/")
async def index():
    """Serve the character sheet frontend."""
    return FileResponse(client_static_dir / "index.html")


@app.get("/character-select")
async def character_select():
    """Serve the character select page."""
    return FileResponse(client_static_dir / "character-select.html")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
