# Data Import Guide

This guide explains how to import D&D 5e game data from 5etools JSON files into Neo4j.

## Overview

The data import system allows you to import races, classes, and backgrounds from 5etools JSON data files. The system supports:

- SRD (Systems Reference Document) filtering
- Idempotent operations (safe to run multiple times)
- Automatic relationship creation in Neo4j
- Legacy content filtering

## Obtaining 5etools Data Files

5etools is a community-maintained resource for D&D 5e content. To obtain the JSON data files:

1. Visit the 5etools repository: https://github.com/5etools-mirror-1/5etools
2. Navigate to the `data` directory
3. Download the following files:
   - `races.json`
   - `classes.json`
   - `backgrounds.json`

Alternatively, you can clone the repository:

```bash
git clone https://github.com/5etools-mirror-1/5etools.git
cp -r 5etools/data/* priv/data/5etools/
```

## Directory Structure

Place the JSON files in the following directory structure:

```
priv/
  data/
    5etools/
      races.json
      classes.json
      backgrounds.json
      README.md
```

The default path is `priv/data/5etools`, but you can specify a custom path when running the import.

## Running the Import

### Basic Import

Import all data files (races, classes, backgrounds):

```bash
mix import.5etools
```

### Custom Path

Import from a custom directory:

```bash
mix import.5etools --path /path/to/your/data
```

Or using the short alias:

```bash
mix import.5etools -p /path/to/your/data
```

### SRD-Only Import

Import only SRD (Systems Reference Document) content, excluding homebrew and non-SRD sources:

```bash
mix import.5etools --srd-only
```

Or using the short alias:

```bash
mix import.5etools -s
```

### Combined Options

You can combine options:

```bash
mix import.5etools --path priv/data/custom --srd-only
```

## SRD Filtering

The SRD filter includes content from these sources:

- `PHB` (Player's Handbook)
- `SRD` (Systems Reference Document)
- `Basic Rules`

Content from other sources (e.g., `XGE`, `TCE`, `Homebrew`) will be excluded when using the `--srd-only` flag.

## What Gets Imported

### Races

- Race name, source, size, speed
- Ability score bonuses
- Subraces and their bonuses
- Legacy content flagging

### Classes

- Class name, source, hit die, primary ability
- Subclasses
- Class features with level requirements

### Backgrounds

- Background name, source
- Skill proficiencies
- Starting equipment
- Background features and traits

## Data Model

The import creates the following Neo4j structure:

```
(Race)-[:HAS_SUBRACE]->(Subrace)
(Class)-[:HAS_SUBCLASS]->(Subclass)
(Class)-[:GRANTS_FEATURE {at_level: X}]->(Feature)
(Character)-[:HAS_RACE]->(Race)
(Character)-[:HAS_CLASS]->(Class)
(Character)-[:HAS_BACKGROUND]->(Background)
```

## Idempotent Operations

The import uses `MERGE` operations, making it safe to run multiple times. If you run the import again:

- Existing nodes will be updated with new data
- New nodes will be created
- Relationships will be maintained or recreated as needed

## Troubleshooting

### File Not Found Errors

If you see errors about missing files:

1. Verify the files exist in the specified directory
2. Check file permissions
3. Ensure the path is correct (use absolute paths if needed)

### JSON Parse Errors

If you encounter JSON parsing errors:

1. Verify the JSON files are valid JSON
2. Check that the files are from the official 5etools repository
3. Ensure files are not corrupted

### Neo4j Connection Errors

If the import fails to connect to Neo4j:

1. Verify Neo4j is running: `docker ps | grep neo4j`
2. Check connection settings in `config/config.exs`
3. Verify environment variables if using them:
   - `NEO4J_URL`
   - `NEO4J_USER`
   - `NEO4J_PASSWORD`

### Import Completes But No Data Appears

1. Check Neo4j browser: `http://localhost:7474`
2. Verify the import actually completed (check logs)
3. Try querying for specific nodes:
   ```cypher
   MATCH (r:Race) RETURN r.name LIMIT 10
   ```

### Schema Errors

If you see constraint or index errors:

1. The schema should be created automatically on application start
2. You can manually run schema setup if needed (check `DndApp.DB.Neo4j.setup_schema/0`)

## Example Queries

After importing, you can query the data in Neo4j:

### List All Races

```cypher
MATCH (r:Race)
WHERE NOT r:Legacy
RETURN r.name, r.source
ORDER BY r.name
```

### Get Race with Subraces

```cypher
MATCH (r:Race {name: "Elf"})-[:HAS_SUBRACE]->(sr:Subrace)
RETURN r.name, collect(sr.name) as subraces
```

### List Classes with Features

```cypher
MATCH (c:Class)-[rel:GRANTS_FEATURE]->(f:Feature)
WHERE rel.at_level = 1
RETURN c.name, f.name
ORDER BY c.name
```

### Find SRD-Only Content

```cypher
MATCH (r:Race)
WHERE r.source IN ["PHB", "SRD", "Basic Rules"]
RETURN r.name, r.source
```

## Best Practices

1. **Backup First**: Before importing, consider backing up your Neo4j database
2. **Test Import**: Run a test import with `--srd-only` first to verify everything works
3. **Incremental Updates**: The import is idempotent, so you can re-run it when data files are updated
4. **Monitor Logs**: Watch the application logs during import for any warnings or errors
5. **Verify Results**: After import, verify data appears correctly in Neo4j browser

## Related Documentation

- [Architecture Documentation](ARCHITECTURE.md) - Graph schema and data model
- [Neo4j Setup Guide](START_WITH_EXISTING_NEO4J.md) - Neo4j configuration
- [Troubleshooting Guide](TROUBLESHOOTING.md) - Common issues and solutions

