"""Game system API routes (classes, races, etc.)."""

from fastapi import APIRouter, Depends

from rpg_graph_vtt.graph.connection import Neo4jConnection
from rpg_graph_vtt.graph.queries import GameSystemQueries
from web.api.dependencies import get_db_connection

router = APIRouter()


@router.get("/classes")
async def list_classes(
    conn: Neo4jConnection = Depends(get_db_connection),
):
    """List all available classes."""
    return GameSystemQueries.get_all_classes(conn)


@router.get("/races")
async def list_races(
    conn: Neo4jConnection = Depends(get_db_connection),
):
    """List all available races."""
    return GameSystemQueries.get_all_races(conn)

