"""Party API routes."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException

from rpg_graph_vtt.graph.connection import Neo4jConnection
from rpg_graph_vtt.graph.queries import PartyQueries
from web.api.dependencies import get_db_connection
from web.api.models.responses import CharacterResponse, PartyResponse

router = APIRouter()


@router.get("/parties", response_model=List[PartyResponse])
async def list_parties(
    conn: Neo4jConnection = Depends(get_db_connection),
) -> List[PartyResponse]:
    """List all parties with their characters."""
    parties_data = PartyQueries.get_all_parties(conn)

    parties = []
    for party_data in parties_data:
        party_name = party_data["name"]
        characters_data = PartyQueries.get_party_characters(party_name, conn)

        characters = [CharacterResponse(**char) for char in characters_data]

        parties.append(PartyResponse(name=party_name, characters=characters))

    return parties


@router.get("/parties/{party_name}", response_model=PartyResponse)
async def get_party(
    party_name: str,
    conn: Neo4jConnection = Depends(get_db_connection),
) -> PartyResponse:
    """Get a specific party by name."""
    characters_data = PartyQueries.get_party_characters(party_name, conn)

    if not characters_data:
        raise HTTPException(status_code=404, detail="Party not found")

    characters = [CharacterResponse(**char) for char in characters_data]
    return PartyResponse(name=party_name, characters=characters)

