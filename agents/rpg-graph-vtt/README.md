# RPG Graph VTT - Graph-Powered D&D 5e Character Management

A Neo4j-backed character management system for Dungeons & Dragons 5th Edition that enables character creation, party viewing, and AI agent integration through a semantic graph database architecture.

## Overview

This system transforms traditional character sheet management by storing all character data, relationships, and game rules as nodes and edges in Neo4j. This graph-native approach enables powerful queries and AI agent reasoning that would be difficult or impossible with traditional relational databases.

### Key Features

- **Graph-Native Storage**: All character data stored as nodes and relationships in Neo4j
- **D&D 5e Compatibility**: Full support for D&D 5e character creation and progression
- **Foundry VTT Interoperability**: Import/export characters in Foundry VTT JSON format
- **AI Agent Integration**: Game Master (GM) Agent and Character Assistant Agent powered by Google ADK
- **Party Management**: View and manage multiple characters as a cohesive party

## Architecture

```
┌─────────────────┐      ┌─────────────────────┐      ┌─────────────────┐
│  Jupyter        │      │   Python Backend     │      │    Neo4j Aura   │
│  Notebooks      │◄────►│   (rpg_graph_vtt)   │◄────►│   Graph Database│
│                 │      │                      │      │                 │
└─────────────────┘      └─────────────────────┘      └─────────────────┘
         │                        │                              │
         │                        │                              │
    Character              Graph Queries                    Game Rules
    Creation              (Cypher)                         & Data
```

## Prerequisites

- Python 3.10+
- Neo4j Aura instance (or self-hosted Neo4j)
- Docker (for Jupyter container development)
- Google Cloud Project (for AI agents, optional)

## Setup

### 1. Environment Configuration

Copy the example environment file and configure your Neo4j connection:

```bash
cp .env.example .env
```

Edit `.env` with your Neo4j credentials:

```
NEO4J_URI=neo4j+s://your-instance.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your-password
```

### 2. Install Dependencies

Using Poetry (recommended):

```bash
poetry install
```

Or using pip:

```bash
pip install -r requirements.txt
```

### 3. Initialize Database Schema

Run the setup notebook to initialize the Neo4j schema:

```bash
# In Docker container
docker exec jupyter jupyter nbconvert --execute notebooks/01_neo4j_setup.ipynb

# Or open in Jupyter
jupyter notebook notebooks/01_neo4j_setup.ipynb
```

This will:
- Create all constraints and indexes (from `database/migrations/`)
- Seed D&D 5e core data (from `database/seeds/`)

## Quick Start - Web Frontend

Start the local web server to view character sheets:

```bash
cd agents/rpg-graph-vtt/web
python server.py
```

Or use the start script:

```bash
./agents/rpg-graph-vtt/web/start.sh
```

Then open your browser to: `http://localhost:8000`

The web interface provides:
- Grid view of all characters
- Party filtering
- Character stats display (HP, AC, abilities)
- Auto-refresh capability

## Usage

### Character Creation

Use the character creation notebook to create new characters:

```python
from rpg_graph_vtt.graph.connection import get_connection
from rpg_graph_vtt.graph.queries import CharacterQueries
from rpg_graph_vtt.models.character import Character, AbilityScores

conn = get_connection()

# Create a character
character = Character(
    uuid=uuid4(),
    name="Aragorn",
    level=1,
    hit_points=12,
    hit_points_max=12,
    armor_class=16,
    proficiency_bonus=2,
    ability_scores=AbilityScores(
        strength=15,
        dexterity=13,
        constitution=14,
        intelligence=12,
        wisdom=10,
        charisma=8
    )
)

# Save to Neo4j
character_data = character.to_neo4j_dict()
character_uuid = CharacterQueries.create_character(character_data, conn)

# Link to class, race, background
CharacterQueries.link_character_to_class(character_uuid, "Fighter", 1, conn)
CharacterQueries.link_character_to_race(character_uuid, "Human", conn)
CharacterQueries.link_character_to_background(character_uuid, "Soldier", conn)
```

### Party Management

View all characters in a party:

```python
from rpg_graph_vtt.graph.queries import PartyQueries

# Get party characters
characters = PartyQueries.get_party_characters("The Fellowship", conn)

for char in characters:
    print(f"{char['name']} - Level {char['level']} {char['classes'][0]['name']}")
```

### AI Agents

#### Game Master (GM) Agent

Query D&D 5e rules using natural language. The GM agent acts as a rules arbitrator:

```python
from rpg_graph_vtt.agent import create_gm_agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

agent = create_gm_agent()
runner = Runner(agent, session_service=InMemorySessionService())

response = await runner.run_async("What spells can a 3rd level Wizard learn?")
print(response.content)
```

#### Character Assistant Agent

Get help with character creation:

```python
from rpg_graph_vtt.agent import create_character_assistant_agent

agent = create_character_assistant_agent()
runner = Runner(agent, session_service=InMemorySessionService())

response = await runner.run_async(
    "I want to create a Fighter. What ability scores should I prioritize?"
)
print(response.content)
```

## Project Structure

```
rpg-graph-vtt/
├── rpg_graph_vtt/          # Core Python package
│   ├── models/             # Pydantic data models
│   ├── graph/              # Neo4j operations
│   │   ├── connection.py  # Database connection
│   │   ├── queries.py     # Cypher query builders
│   │   └── schema.py      # Schema definitions
│   ├── converters/         # Import/export converters
│   ├── tools.py            # AI agent tools
│   ├── agent.py            # Agent definitions
│   └── prompt.py           # Agent prompts
├── notebooks/              # Jupyter notebooks
│   ├── 01_neo4j_setup.ipynb
│   ├── 02_character_creation.ipynb
│   └── 03_party_viewing.ipynb
├── client/                 # Frontend/client code
│   ├── static/            # Static assets
│   │   ├── css/           # Stylesheets
│   │   ├── js/            # JavaScript modules
│   │   ├── docs/          # Frontend documentation
│   │   ├── index.html      # Main character sheet
│   │   └── dice-roller.html # Dice roller demo
│   └── README.md
├── web/                    # Backend API server
│   ├── server.py           # FastAPI server
│   └── start.sh           # Server startup script
├── database/               # Database schema and migrations
│   ├── migrations/        # Neo4j schema migrations (Cypher)
│   ├── seeds/             # Data seeds (D&D 5e content)
│   ├── docs/              # Database documentation
│   └── README.md
├── tests/                  # Unit tests
├── pyproject.toml          # Project configuration
└── README.md              # This file
```

## Neo4j Graph Schema

### Core Nodes

- **Character**: Player characters and NPCs
- **Class**: Character classes (Fighter, Wizard, etc.)
- **Race**: Character races (Human, Elf, etc.)
- **Background**: Character backgrounds
- **Spell**: Spells
- **Item**: Equipment, weapons, armor
- **Feature**: Class features, racial features
- **Party**: Group of characters
- **Campaign**: Campaign/world context

### Key Relationships

- `(:Character)-[:HAS_CLASS]->(:Class)`
- `(:Character)-[:HAS_RACE]->(:Race)`
- `(:Character)-[:OWNS]->(:Item)`
- `(:Character)-[:KNOWS_SPELL]->(:Spell)`
- `(:Character)-[:BELONGS_TO_PARTY]->(:Party)`
- `(:Class)-[:GRANTS_FEATURE]->(:Feature)`
- `(:Class)-[:CAN_LEARN_SPELL]->(:Spell)`

See `spec.md` for complete schema documentation.

## Testing

Run tests using pytest:

```bash
pytest tests/
```

For Docker container testing:

```bash
docker exec jupyter pytest tests/
```

## Development

### Adding New Game Data

1. Create a new seed file in `neo4j/seeds/`
2. Use Cypher CREATE statements
3. Run the seed file using the migration utility

### Extending the Schema

1. Update `neo4j/migrations/001_initial_schema.cypher`
2. Add new constraints/indexes as needed
3. Update Pydantic models in `rpg_graph_vtt/models/`
4. Add query builders in `rpg_graph_vtt/graph/queries.py`

## Foundry VTT Integration

Import characters from Foundry VTT:

```python
from rpg_graph_vtt.converters.foundry import FoundryConverter

# Load Foundry JSON
with open("character.json") as f:
    foundry_data = json.load(f)

# Convert to Character model
character = FoundryConverter.from_foundry_json(foundry_data)

# Save to Neo4j
# ... (use CharacterQueries as shown above)
```

Export to Foundry VTT:

```python
# Get character from Neo4j
character_data = CharacterQueries.get_character_with_relationships(uuid, conn)
character = Character.from_neo4j_record(character_data)

# Convert to Foundry format
foundry_json = FoundryConverter.to_foundry_json(character)

# Save to file
with open("exported_character.json", "w") as f:
    json.dump(foundry_json, f, indent=2)
```

## Future Enhancements

- Real-time collaboration (Socket.io)
- Advanced AI agents (NPC Generator, Quest Weaver)
- Campaign timeline tracking
- Relationship mapping between characters
- Homebrew content support
- Multi-system support (Pathfinder, etc.)

## License

Apache 2.0

## Contributing

This is a prototype system designed for easy porting to production tech stacks. Contributions welcome!

## References

- [Neo4j Documentation](https://neo4j.com/docs/)
- [D&D 5e System Reference Document](https://dnd.wizards.com/resources/systems-reference-document)
- [Foundry VTT Documentation](https://foundryvtt.com/article/system-development/)
- [Google ADK Documentation](https://google.github.io/adk-docs/)

