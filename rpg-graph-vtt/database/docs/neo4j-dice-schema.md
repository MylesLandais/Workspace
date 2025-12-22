# Neo4j Dice Roll Schema

## Node Types

### DiceRoll
Represents a complete dice roll event (e.g., "1d20+5" or "2d6+3").

**Properties:**
- `uuid` (String, unique): Unique identifier for the roll
- `notation` (String): Dice notation string (e.g., "1d20+5", "2d6+3")
- `timestamp` (DateTime): When the roll occurred
- `context` (String, nullable): Roll context (e.g., "Strength Check", "Attack Roll")
- `character_uuid` (String): UUID of character who made the roll
- `total` (Integer): Final calculated total including modifiers
- `created_at` (DateTime): Creation timestamp

**Relationships:**
- `(:Character)-[:MADE_ROLL]->(:DiceRoll)`
- `(:DiceRoll)-[:HAS_RESULT]->(:RollResult)`

### RollResult
Represents an individual die result within a roll.

**Properties:**
- `uuid` (String, unique): Unique identifier for the result
- `die_type` (String): Type of die (d4, d6, d8, d10, d12, d20)
- `value` (Integer): Face value rolled (1 to max for die type)
- `modifier` (Integer): Modifier applied to this die (if distributed)
- `total` (Integer): value + modifier
- `position` (Integer): Order of this die in the roll (0-indexed)

**Relationships:**
- `(:DiceRoll)-[:HAS_RESULT]->(:RollResult)`

## Common Cypher Query Patterns

### Get Character's Recent Rolls
```cypher
MATCH (c:Character {uuid: $character_uuid})-[:MADE_ROLL]->(r:DiceRoll)
RETURN r
ORDER BY r.timestamp DESC
LIMIT 10
```

### Get Party Roll History
```cypher
MATCH (p:Party {name: $party_name})<-[:BELONGS_TO_PARTY]-(c:Character)-[:MADE_ROLL]->(r:DiceRoll)
RETURN r, c.name as character_name
ORDER BY r.timestamp DESC
LIMIT 50
```

### Get Roll with All Results
```cypher
MATCH (r:DiceRoll {uuid: $roll_uuid})-[:HAS_RESULT]->(res:RollResult)
RETURN r, collect(res) as results
```

### Get Critical Hits (Natural 20s)
```cypher
MATCH (c:Character {uuid: $character_uuid})-[:MADE_ROLL]->(r:DiceRoll)-[:HAS_RESULT]->(res:RollResult)
WHERE res.die_type = 'd20' AND res.value = 20
RETURN r, res
ORDER BY r.timestamp DESC
LIMIT 20
```

### Get Roll Statistics for Character
```cypher
MATCH (c:Character {uuid: $character_uuid})-[:MADE_ROLL]->(r:DiceRoll)-[:HAS_RESULT]->(res:RollResult)
WHERE res.die_type = 'd20'
RETURN 
  avg(res.value) as average_roll,
  min(res.value) as min_roll,
  max(res.value) as max_roll,
  count(res) as total_rolls
```

## Indexes and Constraints

```cypher
// Unique constraints
CREATE CONSTRAINT dice_roll_uuid IF NOT EXISTS FOR (r:DiceRoll) REQUIRE r.uuid IS UNIQUE;
CREATE CONSTRAINT roll_result_uuid IF NOT EXISTS FOR (r:RollResult) REQUIRE r.uuid IS UNIQUE;

// Indexes for performance
CREATE INDEX dice_roll_timestamp IF NOT EXISTS FOR (r:DiceRoll) ON (r.timestamp);
CREATE INDEX dice_roll_character IF NOT EXISTS FOR (r:DiceRoll) ON (r.character_uuid);
CREATE INDEX roll_result_value IF NOT EXISTS FOR (r:RollResult) ON (r.value);
```

## Data Model Diagram

```
(:Character)
    |
    |[:MADE_ROLL]
    |
    v
(:DiceRoll {uuid, notation, timestamp, context, total})
    |
    |[:HAS_RESULT]
    |
    v
(:RollResult {uuid, die_type, value, modifier, total})
```

## Migration Notes

- Run migration `002_dice_roll_schema.cypher` to create constraints and indexes
- Existing characters can be linked to rolls via character_uuid
- Roll history can be queried without affecting character data
- Consider archiving old rolls (>30 days) to separate archive database

