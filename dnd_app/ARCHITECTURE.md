# Architecture Documentation

This document describes the property graph architecture, data model, and design patterns used in the D&D Character Builder application.

## Overview

The application uses Neo4j as a property graph database to store D&D 5e character data, game content (races, classes, backgrounds), and their relationships. This design enables:

- Flexible querying of character relationships
- Multi-system support (future: D&D 5e, Pathfinder, etc.)
- Efficient traversal of game content relationships
- Character sheet state stored on relationships

## Property Graph Schema

### Node Types

#### Character Node

Represents a created character.

**Labels**: `Character`

**Properties**:
- `id` (String, Unique): UUID identifier
- `name` (String): Character name
- `level` (Integer): Character level
- `str`, `dex`, `con`, `int`, `wis`, `cha` (Integer): Ability scores
- `str_mod`, `dex_mod`, `con_mod`, `int_mod`, `wis_mod`, `cha_mod` (Integer): Ability modifiers
- `proficiency_bonus` (Integer): Proficiency bonus based on level
- `ac` (Integer): Armor Class
- `max_hp` (Integer): Maximum hit points
- `current_hp` (Integer): Current hit points
- `race` (String): Race name (denormalized for quick access)
- `class` (String): Class name (denormalized)
- `background` (String): Background name (denormalized)
- `skills` (String, JSON): Array of skill proficiencies
- `created_at` (DateTime): Creation timestamp
- `updated_at` (DateTime): Last update timestamp

#### Race Node

Represents a character race.

**Labels**: `Race`, optionally `Legacy`

**Properties**:
- `name` (String, Unique): Race name
- `source` (String): Source book (PHB, SRD, XGE, etc.)
- `size` (String): Creature size (Small, Medium, Large)
- `speed` (Integer): Base movement speed
- `ability_bonuses` (String, JSON): Map of ability bonuses
- `entries` (String, JSON): Race description and features
- `created_at` (DateTime): Creation timestamp
- `updated_at` (DateTime): Last update timestamp

#### Subrace Node

Represents a race subrace.

**Labels**: `Subrace`

**Properties**:
- `name` (String, Unique): Subrace name
- `source` (String): Source book
- `ability_bonuses` (String, JSON): Additional ability bonuses
- `entries` (String, JSON): Subrace description and features

#### Class Node

Represents a character class.

**Labels**: `Class`

**Properties**:
- `name` (String, Unique): Class name
- `source` (String): Source book
- `hit_die` (Integer): Hit die size (6, 8, 10, 12)
- `primary_ability` (String): Primary ability score
- `created_at` (DateTime): Creation timestamp
- `updated_at` (DateTime): Last update timestamp

#### Subclass Node

Represents a class subclass.

**Labels**: `Subclass`

**Properties**:
- `name` (String, Unique): Subclass name
- `source` (String): Source book
- `short_name` (String): Abbreviated name

#### Background Node

Represents a character background.

**Labels**: `Background`

**Properties**:
- `name` (String, Unique): Background name
- `source` (String): Source book
- `entries` (String, JSON): Background description
- `skill_proficiencies` (String, JSON): Array of skill proficiencies
- `starting_equipment` (String, JSON): Starting equipment list
- `created_at` (DateTime): Creation timestamp
- `updated_at` (DateTime): Last update timestamp

#### Feature Node

Represents a class feature or ability.

**Labels**: `Feature`

**Properties**:
- `name` (String, Unique): Feature name
- `level` (Integer): Level at which feature is gained
- `entries` (String, JSON): Feature description

#### Equipment Node

Represents equipment or items (future expansion).

**Labels**: `Equipment`

**Properties**:
- `name` (String, Unique): Equipment name
- `type` (String): Equipment type
- `properties` (String, JSON): Equipment properties

#### Draft Node

Represents an incomplete character draft.

**Labels**: `Draft`

**Properties**:
- `id` (String, Unique): Draft identifier
- `data` (String, JSON): Serialized draft data
- `created_at` (DateTime): Creation timestamp
- `updated_at` (DateTime): Last update timestamp

#### PipelineRun Node

Represents a data pipeline execution run for tracking ETL operations.

**Labels**: `PipelineRun`

**Properties**:
- `timestamp` (DateTime): When the pipeline run started
- `source_repo_commit_hash` (String): Git commit hash from the data source submodule
- `script_version` (String): Version of the ETL script used
- `status` (String): Execution status ("RUNNING", "SUCCESS", "FAILED")
- `nodes_created` (Integer): Count of nodes created in this run
- `relationships_created` (Integer): Count of relationships created in this run
- `start_time` (DateTime): Pipeline start timestamp
- `end_time` (DateTime): Pipeline completion timestamp (null if still running)
- `error_message` (String): Error details if status is "FAILED"

### Relationships

#### Character Relationships

```
(Character)-[:HAS_RACE]->(Race)
(Character)-[:HAS_CLASS]->(Class)
(Character)-[:HAS_BACKGROUND]->(Background)
```

These relationships connect a character to their chosen race, class, and background. The character node also stores denormalized copies of these values for quick access.

#### Race Relationships

```
(Race)-[:HAS_SUBRACE]->(Subrace)
```

Connects races to their available subraces.

#### Class Relationships

```
(Class)-[:HAS_SUBCLASS]->(Subclass)
(Class)-[:GRANTS_FEATURE {at_level: Integer}]->(Feature)
```

- `HAS_SUBCLASS`: Links classes to their subclasses
- `GRANTS_FEATURE`: Links classes to features they grant, with the level stored as a relationship property

#### Cross-Reference Relationships

The data pipeline creates relationships from rich text cross-references found in entries:

```
(ClassFeature)-[:REFERENCES_SPELL]->(Spell)
(ClassFeature)-[:REFERENCES_CLASS]->(Class)
(Feature)-[:REFERENCES_FEAT]->(Feat)
```

These relationships are automatically created during the ETL pipeline's second pass when processing `{@tag Name}` references in rich text entries.

## Graph Traversal Examples

### Find All Characters of a Specific Race

```cypher
MATCH (c:Character)-[:HAS_RACE]->(r:Race {name: "Elf"})
RETURN c.name, c.level, c.class
```

### Get Race with All Subraces

```cypher
MATCH (r:Race {name: "Elf"})-[:HAS_SUBRACE]->(sr:Subrace)
RETURN r.name, collect(sr.name) as subraces
```

### Find All Features for a Class at a Specific Level

```cypher
MATCH (c:Class {name: "Fighter"})-[rel:GRANTS_FEATURE]->(f:Feature)
WHERE rel.at_level <= 3
RETURN f.name, rel.at_level
ORDER BY rel.at_level
```

### Get Complete Character with Relationships

```cypher
MATCH (c:Character {id: $id})
OPTIONAL MATCH (c)-[:HAS_RACE]->(r:Race)
OPTIONAL MATCH (c)-[:HAS_CLASS]->(cl:Class)
OPTIONAL MATCH (c)-[:HAS_BACKGROUND]->(b:Background)
RETURN c, r, cl, b
```

### Find Characters by Class and Level Range

```cypher
MATCH (c:Character)-[:HAS_CLASS]->(cl:Class {name: "Wizard"})
WHERE c.level >= 5 AND c.level <= 10
RETURN c.name, c.level
ORDER BY c.level DESC
```

## Constraints and Indexes

### Unique Constraints

The following unique constraints ensure data integrity:

- `Character.id` - Unique character identifier
- `Race.name` - Unique race names
- `Class.name` - Unique class names
- `Background.name` - Unique background names
- `Subrace.name` - Unique subrace names
- `Feature.name` - Unique feature names
- `Equipment.name` - Unique equipment names

### Indexes

Indexes are created for frequently queried properties:

- `Race.source` - Filter races by source book
- `Class.source` - Filter classes by source book
- `Background.source` - Filter backgrounds by source book
- `Feature.level` - Query features by level

## Multi-System Support Design

The graph schema is designed to support multiple game systems in the future:

1. **System Label**: Add a `System` label to nodes (e.g., `:DnD5e`, `:Pathfinder2e`)
2. **System Property**: Store system identifier in node properties
3. **System-Specific Relationships**: Use system-specific relationship types if needed

Example future structure:

```cypher
(Race:DnD5e {name: "Elf", system: "dnd5e"})
(Race:Pathfinder2e {name: "Elf", system: "pf2e"})
```

## Character Sheet State on Relationships

While the current implementation stores character data primarily on the Character node, the design supports storing state on relationships for:

- **Equipment Slots**: `(Character)-[:EQUIPPED {slot: "main_hand"}]->(Equipment)`
- **Active Features**: `(Character)-[:HAS_ACTIVE {uses_remaining: 2}]->(Feature)`
- **Spell Slots**: `(Character)-[:HAS_SPELL_SLOT {level: 3, remaining: 2}]->(Spell)`

This allows for more flexible querying and state management.

## Query Patterns

### Idempotent Operations

All write operations use `MERGE` to ensure idempotency:

```cypher
MERGE (c:Character {id: $id})
SET c.name = $name,
    c.updated_at = datetime()
ON CREATE SET c.created_at = datetime()
```

### Relationship Creation

Relationships are created with `MERGE` to avoid duplicates:

```cypher
MATCH (c:Character {id: $id})
MATCH (r:Race {name: $race_name})
MERGE (c)-[:HAS_RACE]->(r)
```

### Batch Operations

For importing multiple items:

```cypher
UNWIND $races AS race_data
MERGE (r:Race {name: race_data.name})
SET r.source = race_data.source
```

## Data Flow

1. **Data Import**: 5etools JSON → Parser → Neo4j nodes and relationships
   - **Elixir Import**: Direct import via `mix import.5etools` (see [DATA_IMPORT.md](DATA_IMPORT.md))
   - **Python ETL Pipeline**: Comprehensive ETL with Git submodule tracking and pipeline state management (see [DATA_PIPELINE.md](DATA_PIPELINE.md))
2. **Character Creation**: Wizard UI → Characters context → Neo4j Character node
3. **Character Query**: Neo4j → Characters context → LiveView → UI
4. **Game Content Query**: Neo4j → Characters context → LiveView → UI

## Data Source Tracking

The data pipeline uses Git submodules to provide traceability between imported graph data and its source.

### Git Submodule Integration

The 5e.tools data source is tracked as a Git submodule at `data/5e-source`, which provides:

- **Version Tracking**: Each pipeline run records the exact Git commit hash of the data source
- **Reproducibility**: You can determine which version of the source data was used for any import
- **Audit Trail**: The `PipelineRun` node stores `source_repo_commit_hash` linking back to the source

### Querying Pipeline History

Query the latest import and its source:

```cypher
MATCH (p:PipelineRun)
RETURN p.timestamp, p.source_repo_commit_hash, p.status, p.nodes_created, p.relationships_created
ORDER BY p.timestamp DESC
LIMIT 1
```

Find all imports from a specific source commit:

```cypher
MATCH (p:PipelineRun {source_repo_commit_hash: $commit_hash})
RETURN p
ORDER BY p.timestamp DESC
```

## Performance Considerations

1. **Denormalization**: Character node stores race/class/background names for quick access
2. **Indexes**: Frequently queried properties are indexed
3. **Relationship Direction**: Relationships are directional for efficient traversal
4. **JSON Storage**: Complex nested data stored as JSON strings (trade-off for simplicity)

## Future Enhancements

1. **Spell System**: Add Spell nodes and spell slot relationships
2. **Inventory System**: Equipment nodes with quantity and properties on relationships
3. **Multi-Character Campaigns**: Campaign nodes linking multiple characters
4. **Version History**: Track character changes over time
5. **Templates**: Character template nodes for quick creation

## Future: Ash Framework Integration

The architecture is designed to support Ash Framework integration for declarative resource definitions and GraphQL API generation.

### Ash Resources

Ash Resources will map directly to Neo4j node labels, providing:

- **Declarative Schema**: Define resources with attributes, relationships, and actions
- **Type Safety**: End-to-end type safety from Neo4j through Elixir to GraphQL
- **Automatic GraphQL**: AshGraphql will automatically expose resources via GraphQL

### Example Ash Resource Structure

```elixir
defmodule Kino.RPG.Class do
  use Ash.Resource,
    data_layer: AshNeo4j.DataLayer

  attributes do
    attribute :name, :string, primary_key?: true
    attribute :source, :string
    attribute :hit_die, :integer
    # ... other attributes
  end

  relationships do
    has_many :subclasses, Kino.RPG.Subclass
    has_many :features, Kino.RPG.ClassFeature
  end
end
```

### GraphQL API

AshGraphql will automatically generate GraphQL queries and mutations:

```graphql
query {
  classes {
    name
    source
    subclasses {
      name
    }
    features {
      name
      level
    }
  }
}
```

This provides a type-safe, declarative interface for consuming the graph data stored in Neo4j, with automatic relationship traversal and filtering capabilities.

For detailed information on the Python ETL pipeline that populates this data, see [DATA_PIPELINE.md](DATA_PIPELINE.md).

## Related Documentation

- [Data Pipeline Guide](DATA_PIPELINE.md) - Comprehensive Python ETL pipeline with Git submodule tracking
- [Data Import Guide](DATA_IMPORT.md) - Elixir-based import approach
- [Neo4j Module](lib/dnd_app/db/neo4j.ex) - Database operations
- [Characters Context](lib/dnd_app/characters.ex) - Business logic

