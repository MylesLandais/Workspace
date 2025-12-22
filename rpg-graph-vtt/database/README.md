# Database - Graph Database Schema and Migrations

This directory contains all database-related files: Neo4j migrations, seeds, and documentation.

## Structure

```
database/
├── migrations/        # Neo4j schema migrations (Cypher)
│   ├── 001_initial_schema.cypher      # Initial character/party schema
│   └── 002_dice_roll_schema.cypher    # Dice roll schema
├── seeds/            # Data seeds (D&D 5e content)
│   ├── dnd5e_classes.cypher
│   ├── dnd5e_races.cypher
│   ├── dnd5e_backgrounds.cypher
│   └── dnd5e_spells.cypher
├── schema/           # Programmatic schema definitions
│   ├── constraints.py    # Unique constraint definitions
│   ├── indexes.py        # Index definitions
│   └── relationships.py  # Relationship type definitions
├── docs/             # Database documentation
│   ├── neo4j-dice-schema.md          # Dice roll schema documentation
│   └── valkey-cache-strategy.md      # Cache strategy for Valkey/Redis
└── README.md
```

## Neo4j Migrations

Migrations are Cypher scripts that create constraints, indexes, and schema definitions.

### Programmatic Schema

The `schema/` directory contains Python definitions for:
- **constraints.py**: Unique constraint definitions
- **indexes.py**: Index definitions  
- **relationships.py**: Relationship type metadata

These can be used to generate Cypher statements programmatically or validate schema consistency.

### Running Migrations

```bash
# Using Neo4j Browser or cypher-shell
cat database/migrations/001_initial_schema.cypher | cypher-shell -u neo4j -p password

# Or using Python migration utility
python -m rpg_graph_vtt.graph.migrations run_migration database/migrations/001_initial_schema.cypher
```

### Migration Order

1. `001_initial_schema.cypher` - Base schema (Character, Party, Class, Race, etc.)
2. `002_dice_roll_schema.cypher` - Dice roll nodes and relationships

## Seeds

Seed files populate the database with D&D 5e game content:
- Classes (Fighter, Wizard, etc.)
- Races (Human, Elf, etc.)
- Backgrounds
- Spells

### Running Seeds

```bash
# Using cypher-shell
cat database/seeds/dnd5e_classes.cypher | cypher-shell -u neo4j -p password
```

## Documentation

- **neo4j-dice-schema.md**: Complete schema documentation for dice roll nodes, relationships, and query patterns
- **valkey-cache-strategy.md**: Cache key patterns, TTL policies, and invalidation rules for Valkey/Redis

## Best Practices

1. **Migrations are idempotent**: Use `IF NOT EXISTS` clauses
2. **Version migrations**: Number sequentially (001, 002, etc.)
3. **Document changes**: Update schema docs when adding migrations
4. **Test locally**: Run migrations on local Neo4j before production

## Connection

The Python code in `../rpg_graph_vtt/graph/connection.py` handles Neo4j connections using the Bolt protocol.

