// Dice Roll Schema Migration
// Adds nodes and relationships for dice roll tracking

// Create DiceRoll node constraint
CREATE CONSTRAINT dice_roll_uuid IF NOT EXISTS FOR (r:DiceRoll) REQUIRE r.uuid IS UNIQUE;

// Create RollResult node constraint  
CREATE CONSTRAINT roll_result_uuid IF NOT EXISTS FOR (r:RollResult) REQUIRE r.uuid IS UNIQUE;

// Create indexes for common queries
CREATE INDEX dice_roll_timestamp IF NOT EXISTS FOR (r:DiceRoll) ON (r.timestamp);
CREATE INDEX dice_roll_character IF NOT EXISTS FOR (r:DiceRoll) ON (r.character_uuid);
CREATE INDEX roll_result_value IF NOT EXISTS FOR (r:RollResult) ON (r.value);

// Example: Create a dice roll node
// CREATE (r:DiceRoll {
//   uuid: 'roll-uuid-here',
//   notation: '1d20+5',
//   timestamp: datetime(),
//   context: 'Strength Check',
//   character_uuid: 'character-uuid-here'
// })

// Example: Link character to roll
// MATCH (c:Character {uuid: $character_uuid}), (r:DiceRoll {uuid: $roll_uuid})
// CREATE (c)-[:MADE_ROLL]->(r)

// Example: Create roll result (individual die)
// CREATE (res:RollResult {
//   uuid: 'result-uuid-here',
//   die_type: 'd20',
//   value: 15,
//   modifier: 5,
//   total: 20
// })

// Example: Link roll to results
// MATCH (r:DiceRoll {uuid: $roll_uuid}), (res:RollResult {uuid: $result_uuid})
// CREATE (r)-[:HAS_RESULT]->(res)



