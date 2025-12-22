"""Development utilities and seed data endpoints."""

from pathlib import Path
from typing import Dict

from fastapi import APIRouter, Depends, HTTPException

from rpg_graph_vtt.graph.connection import Neo4jConnection
from rpg_graph_vtt.graph.migrations import run_migration
from web.api.dependencies import get_db_connection

router = APIRouter(prefix="/dev", tags=["development"])


@router.post("/seed-characters")
async def seed_sample_characters(
    conn: Neo4jConnection = Depends(get_db_connection),
) -> Dict[str, str]:
    """
    Seed the database with sample characters.
    
    This endpoint runs the sample_characters.cypher seed file to populate
    the database with test characters (Aragorn, Gandalf, Legolas, etc.).
    """
    project_root = Path(__file__).parent.parent.parent.parent
    seed_file = project_root / "database" / "seeds" / "sample_characters.cypher"
    
    if not seed_file.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Seed file not found: {seed_file}",
        )
    
    try:
        success = run_migration(seed_file, conn)
        if success:
            return {
                "status": "success",
                "message": "Sample characters seeded successfully",
            }
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to seed characters",
            )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error seeding characters: {str(e)}",
        )



