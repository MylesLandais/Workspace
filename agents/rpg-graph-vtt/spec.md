# Graph-Powered D&D 5e Character Management System - Specification

**Version:** 0.1.0  
**Last Updated:** December 2024  
**Status:** MVP Complete - Web Frontend Operational

## Quick Reference

### Current System Capabilities
- ✅ **Neo4j Graph Database**: Full schema with constraints, indexes, and D&D 5e seed data
- ✅ **Character Management**: Create, read, update, delete characters with full relationship tracking
- ✅ **Party Management**: Group characters into parties, view party sheets
- ✅ **Web Frontend**: FastAPI server with HTML/CSS/JS character sheet viewer
- ✅ **AI Agents**: GM Agent (rules lookup) and Character Assistant Agent
- ✅ **Foundry VTT**: Import/export compatibility
- ✅ **Jupyter Notebooks**: Setup, character creation, and party viewing workflows

### Key Files
- `rpg_graph_vtt/graph/connection.py` - Neo4j connection management
- `rpg_graph_vtt/graph/queries.py` - All Cypher query builders
- `rpg_graph_vtt/models/` - Pydantic data models
- `web/server.py` - FastAPI web server
- `web/static/index.html` - Character sheet frontend
- `notebooks/01_neo4j_setup.ipynb` - Database initialization

### Running the System
1. **Setup Neo4j**: Run `notebooks/01_neo4j_setup.ipynb`
2. **Start Web Server**: `cd web && python server.py` or `uvicorn server:app --host 0.0.0.0 --port 8000`
3. **Access Frontend**: `http://localhost:8000`

### Docker Notes
- Workspace mounted at `/home/jovyan/workspace` (singular) in container
- Server runs on port 8000 (expose in docker-compose.yml for external access)
- Neo4j package must be installed: `docker exec jupyter pip install neo4j`

## 1. Executive Summary

This specification defines a graph-powered character management system for Dungeons & Dragons 5th Edition (D&D 5e), built on Neo4j as the single source of truth. The system enables character creation, party management, and AI agent integration through a semantic graph database architecture.

**Current Implementation Status:**
- ✅ Core graph database schema and migrations
- ✅ Character creation and management
- ✅ Party viewing and organization
- ✅ Web frontend with FastAPI server
- ✅ AI agents (GM Agent, Character Assistant)
- ✅ Foundry VTT import/export
- ✅ D&D 5e data seeding (classes, races, backgrounds, spells)

### 1.1 Core Objectives

- **Graph-Native Storage**: All character data, relationships, and game rules stored as nodes and edges in Neo4j
- **D&D 5e Compatibility**: Full support for D&D 5e character creation, progression, and rules
- **Foundry VTT Interoperability**: Import/export characters in Foundry VTT JSON format
- **AI Agent Integration**: Enable AI agents to query and reason over character data using graph traversals
- **Party Management**: View and manage multiple characters as a cohesive party

### 1.2 Architectural Principles

1. **Graph-First Design**: Relationships are first-class citizens, not afterthoughts
2. **Data Hygiene**: Persistent schema with proper constraints and indexes
3. **Prototype-to-Production**: Python/Jupyter prototype designed for easy porting
4. **Rule Fidelity**: All game mechanics validated against D&D 5e ruleset

## 2. Neo4j Graph Schema

### 2.1 Node Labels and Properties

#### Character Nodes

**`(:Character)`**
- `uuid` (String, unique): Unique identifier for the character
- `name` (String): Character name
- `level` (Integer): Total character level
- `hit_points` (Integer): Current hit points
- `hit_points_max` (Integer): Maximum hit points
- `armor_class` (Integer): Armor class
- `proficiency_bonus` (Integer): Proficiency bonus based on level
- `ability_scores` (Map): JSON object with STR, DEX, CON, INT, WIS, CHA values
- `ability_modifiers` (Map): JSON object with calculated modifiers
- `saving_throws` (Map): JSON object with proficiency flags
- `skills` (Map): JSON object with skill proficiencies
- `created_at` (DateTime): Creation timestamp
- `updated_at` (DateTime): Last update timestamp

#### Game System Nodes

**`(:Class)`**
- `name` (String, unique): Class name (e.g., "Fighter", "Wizard")
- `hit_die` (Integer): Hit die size (e.g., 8, 10, 12)
- `primary_ability` (String): Primary ability score (STR, DEX, etc.)
- `saving_throw_proficiencies` (List<String>): List of saving throw proficiencies
- `skill_proficiencies_count` (Integer): Number of skill proficiencies to choose
- `available_skills` (List<String>): List of available skill choices
- `spellcasting_ability` (String, nullable): Ability used for spellcasting (if applicable)
- `subclasses` (List<String>): Available subclasses

**`(:Subclass)`**
- `name` (String): Subclass name
- `parent_class` (String): Parent class name
- `level_obtained` (Integer): Level at which subclass is obtained

**`(:Race)`**
- `name` (String, unique): Race name (e.g., "Human", "Elf", "Dwarf")
- `ability_score_increases` (Map): JSON object with ability score bonuses
- `size` (String): Creature size (Tiny, Small, Medium, Large, Huge)
- `speed` (Integer): Base walking speed in feet
- `traits` (List<String>): Racial traits

**`(:Background)`**
- `name` (String, unique): Background name
- `skill_proficiencies` (List<String>): Granted skill proficiencies
- `tool_proficiencies` (List<String>): Granted tool proficiencies
- `languages` (List<String>): Additional languages
- `equipment` (List<String>): Starting equipment

**`(:Spell)`**
- `name` (String, unique): Spell name
- `level` (Integer): Spell level (0-9, 0=cantrip)
- `school` (String): Magic school (Abjuration, Evocation, etc.)
- `casting_time` (String): Casting time description
- `range` (String): Spell range
- `components` (String): Components (V, S, M)
- `material_components` (String, nullable): Material components description
- `duration` (String): Spell duration
- `description` (String): Spell description
- `higher_levels` (String, nullable): Description of effects at higher levels
- `ritual` (Boolean): Whether spell can be cast as ritual
- `concentration` (Boolean): Whether spell requires concentration

**`(:Item)`**
- `name` (String): Item name
- `type` (String): Item type (weapon, armor, equipment, consumable, etc.)
- `rarity` (String, nullable): Item rarity (common, uncommon, rare, etc.)
- `weight` (Float): Item weight in pounds
- `cost` (Integer): Item cost in gold pieces
- `description` (String): Item description
- `properties` (Map, nullable): JSON object with item-specific properties

**`(:Feature)`**
- `name` (String): Feature name
- `description` (String): Feature description
- `source_type` (String): Source type (class, race, background, feat)
- `level_obtained` (Integer, nullable): Level at which feature is obtained
- `prerequisites` (Map, nullable): JSON object with prerequisites

**`(:Feat)`**
- `name` (String, unique): Feat name
- `description` (String): Feat description
- `prerequisites` (Map, nullable): Prerequisites (ability scores, etc.)
- `benefits` (List<String>): List of benefits granted

#### Campaign Nodes

**`(:Party)`**
- `name` (String, unique): Party name
- `created_at` (DateTime): Creation timestamp
- `description` (String, nullable): Party description

**`(:Campaign)`**
- `name` (String, unique): Campaign name
- `setting` (String, nullable): Campaign setting
- `created_at` (DateTime): Creation timestamp

### 2.2 Relationship Types

#### Character Relationships

- `(:Character)-[:HAS_CLASS {level: Integer}]->(:Class)`
  - Represents a character's class and level in that class
  - Properties: `level` (level in this specific class)

- `(:Character)-[:HAS_SUBCLASS]->(:Subclass)`
  - Links character to their chosen subclass

- `(:Character)-[:HAS_RACE]->(:Race)`
  - Links character to their race

- `(:Character)-[:HAS_BACKGROUND]->(:Background)`
  - Links character to their background

- `(:Character)-[:OWNS {equipped: Boolean, quantity: Integer}]->(:Item)`
  - Represents character inventory
  - Properties: `equipped` (whether item is currently equipped), `quantity` (number owned)

- `(:Character)-[:KNOWS_SPELL {prepared: Boolean, source: String}]->(:Spell)`
  - Represents known/prepared spells
  - Properties: `prepared` (whether spell is prepared), `source` (class, race, feat, etc.)

- `(:Character)-[:HAS_FEATURE]->(:Feature)`
  - Links character to features they possess

- `(:Character)-[:HAS_FEAT]->(:Feat)`
  - Links character to feats they have taken

- `(:Character)-[:BELONGS_TO_PARTY]->(:Party)`
  - Links character to a party

#### Game System Relationships

- `(:Class)-[:GRANTS_FEATURE {level: Integer}]->(:Feature)`
  - Links class to features granted at specific levels
  - Properties: `level` (level at which feature is granted)

- `(:Subclass)-[:GRANTS_FEATURE {level: Integer}]->(:Feature)`
  - Links subclass to features granted at specific levels

- `(:Race)-[:GRANTS_FEATURE]->(:Feature)`
  - Links race to racial features

- `(:Background)-[:GRANTS_FEATURE]->(:Feature)`
  - Links background to background features

- `(:Class)-[:CAN_LEARN_SPELL]->(:Spell)`
  - Indicates spells available to a class

- `(:Spell)-[:REQUIRES_CLASS]->(:Class)`
  - Indicates class requirements for spells

- `(:Item)-[:REQUIRES_ATTUNEMENT]->(:Character)`
  - Represents attunement requirements (for magic items)

- `(:Party)-[:HAS_CAMPAIGN]->(:Campaign)`
  - Links party to campaign

### 2.3 Indexes and Constraints

```cypher
// Unique constraints
CREATE CONSTRAINT character_uuid IF NOT EXISTS FOR (c:Character) REQUIRE c.uuid IS UNIQUE;
CREATE CONSTRAINT class_name IF NOT EXISTS FOR (c:Class) REQUIRE c.name IS UNIQUE;
CREATE CONSTRAINT race_name IF NOT EXISTS FOR (r:Race) REQUIRE r.name IS UNIQUE;
CREATE CONSTRAINT background_name IF NOT EXISTS FOR (b:Background) REQUIRE b.name IS UNIQUE;
CREATE CONSTRAINT spell_name IF NOT EXISTS FOR (s:Spell) REQUIRE s.name IS UNIQUE;
CREATE CONSTRAINT party_name IF NOT EXISTS FOR (p:Party) REQUIRE p.name IS UNIQUE;
CREATE CONSTRAINT campaign_name IF NOT EXISTS FOR (c:Campaign) REQUIRE c.name IS UNIQUE;

// Indexes for common queries
CREATE INDEX character_name IF NOT EXISTS FOR (c:Character) ON (c.name);
CREATE INDEX character_level IF NOT EXISTS FOR (c:Character) ON (c.level);
CREATE INDEX spell_level IF NOT EXISTS FOR (s:Spell) ON (s.level);
CREATE INDEX item_type IF NOT EXISTS FOR (i:Item) ON (i.type);
```

## 3. Data Models (Pydantic)

### 3.1 Character Model

```python
from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from datetime import datetime
from uuid import UUID

class AbilityScores(BaseModel):
    strength: int = Field(ge=1, le=30)
    dexterity: int = Field(ge=1, le=30)
    constitution: int = Field(ge=1, le=30)
    intelligence: int = Field(ge=1, le=30)
    wisdom: int = Field(ge=1, le=30)
    charisma: int = Field(ge=1, le=30)

class Character(BaseModel):
    uuid: UUID
    name: str
    level: int = Field(ge=1, le=20)
    hit_points: int
    hit_points_max: int
    armor_class: int
    proficiency_bonus: int
    ability_scores: AbilityScores
    ability_modifiers: Dict[str, int]
    saving_throws: Dict[str, bool]
    skills: Dict[str, bool]
    created_at: datetime
    updated_at: datetime
```

### 3.2 Game System Models

```python
class Class(BaseModel):
    name: str
    hit_die: int
    primary_ability: str
    saving_throw_proficiencies: List[str]
    skill_proficiencies_count: int
    available_skills: List[str]
    spellcasting_ability: Optional[str] = None
    subclasses: List[str] = []

class Race(BaseModel):
    name: str
    ability_score_increases: Dict[str, int]
    size: str
    speed: int
    traits: List[str] = []

class Spell(BaseModel):
    name: str
    level: int = Field(ge=0, le=9)
    school: str
    casting_time: str
    range: str
    components: str
    material_components: Optional[str] = None
    duration: str
    description: str
    higher_levels: Optional[str] = None
    ritual: bool = False
    concentration: bool = False
```

## 4. API Design

### 4.1 Character Operations ✅ IMPLEMENTED

**Implementation:** `rpg_graph_vtt/graph/queries.py::CharacterQueries`

**Create Character**
```python
CharacterQueries.create_character(character_data: Dict, connection: Neo4jConnection) -> UUID
```
Creates character node and returns UUID.

**Get Character**
```python
CharacterQueries.get_character(uuid: UUID, connection: Neo4jConnection) -> Optional[Dict]
CharacterQueries.get_character_with_relationships(uuid: UUID, connection: Neo4jConnection) -> Optional[Dict]
```
Retrieves character with optional relationship data (classes, races, items, spells).

**Update Character**
```python
CharacterQueries.update_character(uuid: UUID, updates: Dict, connection: Neo4jConnection) -> bool
```
Updates character properties dynamically.

**Delete Character**
```python
CharacterQueries.delete_character(uuid: UUID, connection: Neo4jConnection) -> bool
```
Deletes character and all relationships.

**Link Operations**
- `link_character_to_class(character_uuid, class_name, level, connection)`
- `link_character_to_race(character_uuid, race_name, connection)`
- `link_character_to_background(character_uuid, background_name, connection)`
- `add_item_to_character(character_uuid, item_name, equipped, quantity, connection)`

### 4.2 Party Operations ✅ IMPLEMENTED

**Implementation:** `rpg_graph_vtt/graph/queries.py::PartyQueries`

**Create Party**
```python
PartyQueries.create_party(party_data: Dict, connection: Neo4jConnection) -> str
```

**Add Character to Party**
```python
PartyQueries.add_character_to_party(character_uuid: UUID, party_name: str, connection: Neo4jConnection) -> bool
```

**Get Party Characters**
```python
PartyQueries.get_party_characters(party_name: str, connection: Neo4jConnection) -> List[Dict]
```
Returns all characters in party with full relationship data.

**Get All Parties**
```python
PartyQueries.get_all_parties(connection: Neo4jConnection) -> List[Dict]
```

### 4.3 Game System Queries ✅ IMPLEMENTED

**Implementation:** `rpg_graph_vtt/graph/queries.py::GameSystemQueries`

**Class Operations**
- `get_class(class_name: str, connection) -> Optional[Dict]`
- `get_all_classes(connection) -> List[Dict]`

**Race Operations**
- `get_race(race_name: str, connection) -> Optional[Dict]`
- `get_all_races(connection) -> List[Dict]`

**Spell Operations**
- `get_available_spells(class_name: str, level: int, connection) -> List[Dict]`

**Character Search**
- `find_characters_by_class(class_name: str, connection) -> List[Dict]`

### 4.4 Web API Endpoints ✅ IMPLEMENTED

**Implementation:** `web/server.py`

**REST Endpoints:**
- `GET /api/characters` - List all characters (returns `List[CharacterResponse]`)
- `GET /api/characters/{uuid}` - Get specific character
- `GET /api/parties` - List all parties with characters
- `GET /api/parties/{name}` - Get specific party
- `GET /api/classes` - List all classes
- `GET /api/races` - List all races

**Response Models:**
- `CharacterResponse` - Character with relationships
- `PartyResponse` - Party with character list

## 5. Import/Export Formats

### 5.1 Foundry VTT Format

The system supports importing and exporting characters in Foundry VTT's actor JSON format. Key mappings:

- `actor.name` → `Character.name`
- `actor.data.level` → `Character.level`
- `actor.data.attributes.hp` → `Character.hit_points`
- `actor.data.abilities.*.value` → `Character.ability_scores`
- `actor.items` → `Character` relationships to `Item` and `Spell` nodes

### 5.2 D&D 5e Schema Format

Support for standard D&D 5e JSON schema with mappings to graph nodes.

## 6. AI Agent Integration

### 6.1 Game Master (GM) Agent ✅ IMPLEMENTED

The GM agent queries Neo4j to answer questions about D&D 5e rules. Implemented in `rpg_graph_vtt/agent.py`:

**Features:**
- Query character information by name
- Query available spells for classes at specific levels
- Query class features by level
- Query multiclass prerequisites
- Query party information

**Usage:**
```python
from rpg_graph_vtt.agent import create_gm_agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

agent = create_gm_agent()
runner = Runner(agent, session_service=InMemorySessionService())
response = await runner.run_async("What spells can a 3rd level Wizard learn?")
```

**Tools Available:**
- `query_character_info(character_name: str)` - Get character details
- `query_available_spells(class_name: str, level: int)` - Get spells for class/level
- `query_class_features(class_name: str, level: int)` - Get features for class/level
- `query_multiclass_prerequisites(class_name: str)` - Get multiclass requirements
- `query_party_characters(party_name: str)` - Get all characters in party

### 6.2 Character Assistant Agent ✅ IMPLEMENTED

Helps with character creation. Implemented in `rpg_graph_vtt/agent.py`:

**Features:**
- Suggests optimal ability score distributions
- Recommends equipment based on class
- Validates multiclass prerequisites
- Suggests spells based on build
- Validates character builds against D&D 5e rules

**Usage:**
```python
from rpg_graph_vtt.agent import create_character_assistant_agent

agent = create_character_assistant_agent()
runner = Runner(agent, session_service=InMemorySessionService())
response = await runner.run_async(
    "I want to create a Fighter. What ability scores should I prioritize?"
)
```

**Additional Tools:**
- `validate_character_build(class_name, race_name, ability_scores)` - Validate build compliance

## 7. Implementation Status

### Phase 1: Foundation ✅ COMPLETE
- [x] Project structure
- [x] Neo4j schema design
- [x] Neo4j connection utilities (`rpg_graph_vtt/graph/connection.py`)
- [x] Basic data models (Character, Party, Class, Race, Background, Spell, Item, Feature)
- [x] Graph query builders (`rpg_graph_vtt/graph/queries.py`)
- [x] Schema migrations (`neo4j/migrations/001_initial_schema.cypher`)

### Phase 2: Character Creation ✅ COMPLETE
- [x] D&D 5e data seeding (classes, races, backgrounds, spells)
- [x] Character creation workflow (`notebooks/02_character_creation.ipynb`)
- [x] Foundry VTT import/export (`rpg_graph_vtt/converters/foundry.py`)
- [x] Derived stat calculations (proficiency bonus, ability modifiers)

### Phase 3: Party Management ✅ COMPLETE
- [x] Party creation and management (`rpg_graph_vtt/graph/queries.py::PartyQueries`)
- [x] Party viewing interface (`notebooks/03_party_viewing.ipynb`)
- [x] Web frontend for character sheet viewing (`web/static/index.html`)

### Phase 4: AI Agents ✅ COMPLETE
- [x] Game Master (GM) Agent (formerly Rules Lookup Agent)
- [x] Character Assistant Agent
- [x] Integration with Google ADK (`rpg_graph_vtt/agent.py`)
- [x] Agent tools for graph database interaction (`rpg_graph_vtt/tools.py`)

### Phase 5: Web Frontend ✅ COMPLETE
- [x] FastAPI server (`web/server.py`)
- [x] REST API endpoints for characters, parties, classes, races
- [x] HTML/CSS/JS frontend with character card grid view
- [x] Party filtering and character stats display
- [x] Docker integration and deployment

### Phase 6: Production Readiness 🚧 IN PROGRESS
- [x] Basic error handling
- [x] Neo4j API compatibility (fixed transaction scope issues)
- [ ] Comprehensive testing suite
- [ ] Performance optimization
- [x] Documentation (README.md, spec.md)

## 8. Testing Strategy

### 8.1 Unit Tests
- Graph query functions
- Data model validation
- Import/export converters

### 8.2 Integration Tests
- Full character creation workflow
- Party management operations
- Neo4j transaction handling

### 8.3 Notebook Tests
- Executable examples in Jupyter
- Interactive character creation demos
- Query visualization

## 9. Environment Configuration

### Required Environment Variables

In `~/workspace/.env` (or `~/.env`):
```
NEO4J_URI=neo4j+s://your-instance.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your-password
```

### Docker Container Setup

The workspace is mounted at `/home/jovyan/workspace` (singular) in the Docker container, despite `docker-compose.yml` showing `workspaces` (plural). This is the actual mount point used.

### Dependencies

Core dependencies (installed in container):
- `neo4j>=6.0.0` - Neo4j Python driver
- `fastapi>=0.100.0` - Web framework
- `uvicorn[standard]>=0.23.0` - ASGI server
- `pydantic>=2.0.0` - Data validation
- `python-dotenv>=1.0.0` - Environment variable loading
- `google-adk>=1.0.0` - Agent Development Kit

### Neo4j API Compatibility

The system uses Neo4j 6.x API with `execute_read()` and `execute_write()` methods. Results are consumed within transaction scope to avoid `ResultConsumedError`.

## 10. Web Frontend Architecture

### FastAPI Server (`web/server.py`)

**Endpoints:**
- `GET /` - Character sheet frontend (HTML)
- `GET /api/characters` - List all characters
- `GET /api/characters/{uuid}` - Get specific character
- `GET /api/parties` - List all parties with characters
- `GET /api/parties/{name}` - Get specific party
- `GET /api/classes` - List all classes
- `GET /api/races` - List all races

**Features:**
- Serves static HTML/CSS/JS frontend
- RESTful API for character data
- Real-time data from Neo4j
- Error handling and validation

### Frontend (`web/static/index.html`)

**Features:**
- Responsive character card grid layout
- Party filtering dropdown
- Character stats display (HP, AC, Proficiency Bonus)
- Ability scores with modifiers
- Class, race, and background information
- Auto-refresh capability

**Running the Server:**

From Docker container:
```bash
docker exec -d jupyter bash -c "cd /home/jovyan/workspace/agents/rpg-graph-vtt/web && uvicorn server:app --host 0.0.0.0 --port 8000"
```

From host machine:
```bash
cd agents/rpg-graph-vtt/web
python server.py
```

Access at: `http://localhost:8000` (after exposing port 8000 in docker-compose.yml)

## 11. Current File Structure

```
agents/rpg-graph-vtt/
├── rpg_graph_vtt/              # Core Python package
│   ├── models/                 # Pydantic data models
│   │   ├── character.py        # Character, AbilityScores
│   │   ├── party.py            # Party, Campaign
│   │   └── game_system.py      # Class, Race, Background, Spell, Item, Feature
│   ├── graph/                   # Neo4j operations
│   │   ├── connection.py       # Database connection management
│   │   ├── queries.py          # Cypher query builders
│   │   ├── schema.py           # Schema definitions
│   │   └── migrations.py       # Migration utilities
│   ├── converters/             # Import/export
│   │   ├── foundry.py          # Foundry VTT JSON converter
│   │   └── dnd5e.py            # D&D 5e schema converter
│   ├── tools.py                # AI agent tools
│   ├── agent.py                # Agent definitions (GM, Character Assistant)
│   └── prompt.py               # Agent prompts
├── notebooks/                   # Jupyter notebooks
│   ├── 01_neo4j_setup.ipynb    # Database setup (compact, single cell)
│   ├── 02_character_creation.ipynb  # Character creation workflow
│   └── 03_party_viewing.ipynb  # Party management
├── neo4j/
│   ├── migrations/             # Schema migrations
│   │   └── 001_initial_schema.cypher
│   └── seeds/                  # D&D 5e data seeds
│       ├── dnd5e_classes.cypher
│       ├── dnd5e_races.cypher
│       ├── dnd5e_backgrounds.cypher
│       └── dnd5e_spells.cypher
├── web/                        # Web frontend
│   ├── server.py               # FastAPI server
│   ├── static/
│   │   └── index.html          # Character sheet frontend
│   └── templates/              # (reserved for future use)
├── tests/                      # Unit tests (to be implemented)
├── pyproject.toml              # Project dependencies
├── README.md                   # User documentation
└── spec.md                     # This specification document
```

## 12. Known Issues and Solutions

### Issue: Neo4j Transaction Scope
**Problem:** Results consumed outside transaction scope caused `ResultConsumedError`  
**Solution:** Consume results within transaction using `list(tx.run(...))` pattern

### Issue: Docker Mount Path Mismatch
**Problem:** `docker-compose.yml` shows `workspaces` but actual mount is `workspace`  
**Solution:** Use `/home/jovyan/workspace` path in Docker commands

### Issue: Missing Dependencies
**Problem:** Neo4j package not installed in container  
**Solution:** Install via `docker exec jupyter pip install neo4j`

## 13. Future Enhancements

- Real-time collaboration (Socket.io)
- Advanced AI agents (NPC Generator, Quest Weaver)
- Campaign timeline tracking
- Relationship mapping between characters
- Homebrew content support
- Multi-system support (Pathfinder, etc.)
- Character sheet editing interface
- Spell management UI
- Inventory management
- Dice roller integration
- Session notes and campaign logs

