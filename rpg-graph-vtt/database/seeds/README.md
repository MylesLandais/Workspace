# Database Seeds

This directory contains seed data files for populating the Neo4j database with sample content.

## Available Seeds

### Game System Data
- `dnd5e_classes.cypher` - D&D 5e classes (Fighter, Wizard, etc.)
- `dnd5e_races.cypher` - D&D 5e races (Human, Elf, Dwarf, etc.)
- `dnd5e_backgrounds.cypher` - D&D 5e backgrounds
- `dnd5e_spells.cypher` - D&D 5e spells

### Sample Characters
- `sample_characters.cypher` - Sample characters for testing and demo

## Running Seeds

### Using Cypher Shell

```bash
# Seed game system data first
cat database/seeds/dnd5e_classes.cypher | cypher-shell -u neo4j -p password
cat database/seeds/dnd5e_races.cypher | cypher-shell -u neo4j -p password
cat database/seeds/dnd5e_backgrounds.cypher | cypher-shell -u neo4j -p password

# Then seed sample characters
cat database/seeds/sample_characters.cypher | cypher-shell -u neo4j -p password
```

### Using Python Migration Utility

```python
from rpg_graph_vtt.graph.migrations import run_migration
from pathlib import Path

seed_file = Path("database/seeds/sample_characters.cypher")
run_migration(seed_file)
```

### Using API Endpoint (Development)

After starting the web server, you can seed sample characters via API:

```bash
curl -X POST http://localhost:8000/api/dev/seed-characters
```

Or visit: `http://localhost:8000/docs` and use the Swagger UI to call the endpoint.

## Sample Characters

The `sample_characters.cypher` file creates:

1. **Aragorn** - Level 10 Human Ranger (Folk Hero)
2. **Gandalf** - Level 15 Human Wizard (Sage)
3. **Legolas** - Level 8 Elf Ranger (Outlander)
4. **Gimli** - Level 9 Dwarf Fighter (Soldier)
5. **Arwen** - Level 7 Elf Cleric (Noble)

All characters are added to the "Fellowship of the Ring" party.

## Prerequisites

Before seeding sample characters, ensure:
1. Game system data is seeded (classes, races, backgrounds)
2. Database schema is migrated (run `001_initial_schema.cypher`)

## Notes

- Seeds are idempotent where possible (using `MERGE` or checking existence)
- Sample characters use fixed UUIDs for consistency
- Characters are linked to existing game system nodes (classes, races, backgrounds)



