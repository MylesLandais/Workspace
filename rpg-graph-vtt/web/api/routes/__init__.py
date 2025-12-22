"""API route modules."""

from fastapi import APIRouter

from web.api.routes import characters, game_system, parties, dev

# Create main API router
api_router = APIRouter(prefix="/api")

# Include sub-routers
api_router.include_router(characters.router, tags=["characters"])
api_router.include_router(parties.router, tags=["parties"])
api_router.include_router(game_system.router, tags=["game-system"])
api_router.include_router(dev.router, tags=["development"])

__all__ = ["api_router"]

