"""Character API routes."""

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from rpg_graph_vtt.graph.connection import Neo4jConnection
from rpg_graph_vtt.graph.queries import CharacterQueries
from web.api.dependencies import get_db_connection
from web.api.models.responses import CharacterResponse

router = APIRouter()


@router.get("/characters", response_model=List[CharacterResponse])
async def list_characters(
    conn: Neo4jConnection = Depends(get_db_connection),
) -> List[CharacterResponse]:
    """List all characters."""
    query = "MATCH (c:Character) RETURN c ORDER BY c.name"
    result = conn.execute_read(query)

    characters = []
    for record in result:
        char_data = dict(record["c"])
        char_uuid = char_data.get("uuid")

        if not char_uuid:
            continue

        # Get full character with relationships
        try:
            uuid_obj = UUID(char_uuid) if isinstance(char_uuid, str) else char_uuid
            full_char = CharacterQueries.get_character_with_relationships(uuid_obj, conn)
            if full_char:
                characters.append(CharacterResponse(**full_char))
        except (ValueError, TypeError) as e:
            print(f"Error processing character {char_uuid}: {e}")
            continue

    return characters


@router.get("/characters/{character_uuid}", response_model=CharacterResponse)
async def get_character(
    character_uuid: str,
    conn: Neo4jConnection = Depends(get_db_connection),
) -> CharacterResponse:
    """Get a specific character by UUID."""
    try:
        uuid_obj = UUID(character_uuid)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID format")

    char_data = CharacterQueries.get_character_with_relationships(uuid_obj, conn)
    if not char_data:
        raise HTTPException(status_code=404, detail="Character not found")

    return CharacterResponse(**char_data)

