# Migration Guidelines

This directory contains Neo4j schema migrations in Cypher format.

## Migration Naming

Migrations are numbered sequentially:
- `001_initial_schema.cypher`
- `002_dice_roll_schema.cypher`
- `003_<description>.cypher`

## Best Practices

1. **Idempotent Operations**: Always use `IF NOT EXISTS` clauses
   ```cypher
   CREATE CONSTRAINT character_uuid IF NOT EXISTS FOR (c:Character) REQUIRE c.uuid IS UNIQUE;
   ```

2. **Atomic Statements**: Each statement should be complete and independent

3. **Documentation**: Include comments explaining what each migration does

4. **Testing**: Test migrations on a local Neo4j instance before applying to production

## Running Migrations

### Using Python Utility

```python
from rpg_graph_vtt.graph.migrations import run_all_migrations

# Run all migrations in order
run_all_migrations()
```

### Using Cypher Shell

```bash
cat database/migrations/001_initial_schema.cypher | cypher-shell -u neo4j -p password
```

## Migration Order

Migrations are executed in alphabetical order by filename. Ensure proper sequencing:
- Base schema first (001)
- Feature additions follow (002, 003, etc.)

## Rollback

Currently, migrations do not support automatic rollback. To rollback:
1. Manually create reverse migration (e.g., `002_rollback_dice_roll.cypher`)
2. Or manually drop constraints/indexes in Neo4j Browser

Future enhancements may include version tracking and automatic rollback support.

