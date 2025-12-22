"""FastAPI server for RPG Graph VTT character sheet frontend."""

import sys
from pathlib import Path
from typing import List, Optional
from uuid import UUID

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Add project root to path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from rpg_graph_vtt.graph.connection import get_connection
from rpg_graph_vtt.graph.queries import CharacterQueries, PartyQueries, GameSystemQueries

app = FastAPI(title="RPG Graph VTT", version="0.1.0")

# Mount static files from client directory
project_root = Path(__file__).parent.parent
client_static_dir = project_root / "client" / "static"
app.mount("/static", StaticFiles(directory=client_static_dir), name="static")


# Response models
class CharacterResponse(BaseModel):
    uuid: str
    name: str
    level: int
    hit_points: int
    hit_points_max: int
    armor_class: int
    proficiency_bonus: int
    ability_scores: dict
    ability_modifiers: dict
    saving_throws: dict
    skills: dict
    classes: List[dict] = []
    races: List[dict] = []
    backgrounds: List[dict] = []
    items: List[dict] = []


class PartyResponse(BaseModel):
    name: str
    characters: List[CharacterResponse]


@app.get("/", response_class=HTMLResponse)
async def index():
    """Serve the character sheet frontend."""
    return FileResponse(client_static_dir / "index.html")


@app.get("/api/characters", response_model=List[CharacterResponse])
async def list_characters():
    """List all characters."""
    conn = get_connection()
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


@app.get("/api/characters/{character_uuid}", response_model=CharacterResponse)
async def get_character(character_uuid: str):
    """Get a specific character by UUID."""
    conn = get_connection()
    try:
        uuid_obj = UUID(character_uuid)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID format")
    
    char_data = CharacterQueries.get_character_with_relationships(uuid_obj, conn)
    if not char_data:
        raise HTTPException(status_code=404, detail="Character not found")
    
    return CharacterResponse(**char_data)


@app.get("/api/parties", response_model=List[PartyResponse])
async def list_parties():
    """List all parties with their characters."""
    conn = get_connection()
    parties_data = PartyQueries.get_all_parties(conn)
    
    parties = []
    for party_data in parties_data:
        party_name = party_data["name"]
        characters_data = PartyQueries.get_party_characters(party_name, conn)
        
        characters = [
            CharacterResponse(**char) for char in characters_data
        ]
        
        parties.append(PartyResponse(
            name=party_name,
            characters=characters
        ))
    
    return parties


@app.get("/api/parties/{party_name}", response_model=PartyResponse)
async def get_party(party_name: str):
    """Get a specific party by name."""
    conn = get_connection()
    characters_data = PartyQueries.get_party_characters(party_name, conn)
    
    if not characters_data:
        raise HTTPException(status_code=404, detail="Party not found")
    
    characters = [CharacterResponse(**char) for char in characters_data]
    return PartyResponse(name=party_name, characters=characters)


@app.get("/api/classes")
async def list_classes():
    """List all available classes."""
    conn = get_connection()
    return GameSystemQueries.get_all_classes(conn)


@app.get("/api/races")
async def list_races():
    """List all available races."""
    conn = get_connection()
    return GameSystemQueries.get_all_races(conn)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)

