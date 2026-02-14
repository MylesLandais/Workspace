"""VTT API routes wrapping lib/vtt models and graph."""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List

from lib.vtt.models.character import AbilityScores

router = APIRouter(tags=["vtt"])


@router.get("/characters")
async def list_characters(
    limit: int = Query(50, ge=1, le=200),
    campaign: Optional[str] = None,
):
    """List characters, optionally filtered by campaign."""
    # Placeholder: will query via lib/vtt/graph once AGE backend is wired
    return {"characters": [], "limit": limit, "campaign": campaign}


@router.get("/characters/{character_id}")
async def get_character(character_id: str):
    """Get a character by ID."""
    return {"id": character_id, "status": "stub"}


@router.post("/characters")
async def create_character(name: str, level: int = 1):
    """Create a new character."""
    return {"name": name, "level": level, "status": "created"}


@router.get("/game-systems")
async def list_game_systems():
    """List available game systems."""
    return {"systems": ["dnd5e"]}


@router.get("/parties")
async def list_parties():
    """List parties."""
    return {"parties": []}
