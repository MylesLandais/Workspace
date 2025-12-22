// Initial Neo4j Schema Migration for D&D 5e Character Management System
// This script creates all constraints, indexes, and initial structure

// ============================================================================
// UNIQUE CONSTRAINTS
// ============================================================================

CREATE CONSTRAINT character_uuid IF NOT EXISTS FOR (c:Character) REQUIRE c.uuid IS UNIQUE;
CREATE CONSTRAINT class_name IF NOT EXISTS FOR (c:Class) REQUIRE c.name IS UNIQUE;
CREATE CONSTRAINT race_name IF NOT EXISTS FOR (r:Race) REQUIRE r.name IS UNIQUE;
CREATE CONSTRAINT background_name IF NOT EXISTS FOR (b:Background) REQUIRE b.name IS UNIQUE;
CREATE CONSTRAINT spell_name IF NOT EXISTS FOR (s:Spell) REQUIRE s.name IS UNIQUE;
CREATE CONSTRAINT feat_name IF NOT EXISTS FOR (f:Feat) REQUIRE f.name IS UNIQUE;
CREATE CONSTRAINT party_name IF NOT EXISTS FOR (p:Party) REQUIRE p.name IS UNIQUE;
CREATE CONSTRAINT campaign_name IF NOT EXISTS FOR (c:Campaign) REQUIRE c.name IS UNIQUE;

// ============================================================================
// INDEXES FOR PERFORMANCE
// ============================================================================

CREATE INDEX character_name IF NOT EXISTS FOR (c:Character) ON (c.name);
CREATE INDEX character_level IF NOT EXISTS FOR (c:Character) ON (c.level);
CREATE INDEX spell_level IF NOT EXISTS FOR (s:Spell) ON (s.level);
CREATE INDEX spell_school IF NOT EXISTS FOR (s:Spell) ON (s.school);
CREATE INDEX item_type IF NOT EXISTS FOR (i:Item) ON (i.type);
CREATE INDEX item_rarity IF NOT EXISTS FOR (i:Item) ON (i.rarity);

// ============================================================================
// SCHEMA DOCUMENTATION
// ============================================================================

// Character Node Structure:
// (:Character {
//   uuid: String (unique),
//   name: String,
//   level: Integer (1-20),
//   hit_points: Integer,
//   hit_points_max: Integer,
//   armor_class: Integer,
//   proficiency_bonus: Integer,
//   ability_scores: Map {str, dex, con, int, wis, cha},
//   ability_modifiers: Map {str, dex, con, int, wis, cha},
//   saving_throws: Map {str, dex, con, int, wis, cha},
//   skills: Map {skill_name: Boolean},
//   created_at: DateTime,
//   updated_at: DateTime
// })

// Class Node Structure:
// (:Class {
//   name: String (unique),
//   hit_die: Integer,
//   primary_ability: String,
//   saving_throw_proficiencies: List[String],
//   skill_proficiencies_count: Integer,
//   available_skills: List[String],
//   spellcasting_ability: String (nullable),
//   subclasses: List[String]
// })

// Race Node Structure:
// (:Race {
//   name: String (unique),
//   ability_score_increases: Map {ability: Integer},
//   size: String,
//   speed: Integer,
//   traits: List[String]
// })

// Background Node Structure:
// (:Background {
//   name: String (unique),
//   skill_proficiencies: List[String],
//   tool_proficiencies: List[String],
//   languages: List[String],
//   equipment: List[String]
// })

// Spell Node Structure:
// (:Spell {
//   name: String (unique),
//   level: Integer (0-9),
//   school: String,
//   casting_time: String,
//   range: String,
//   components: String,
//   material_components: String (nullable),
//   duration: String,
//   description: String,
//   higher_levels: String (nullable),
//   ritual: Boolean,
//   concentration: Boolean
// })

// Item Node Structure:
// (:Item {
//   name: String,
//   type: String,
//   rarity: String (nullable),
//   weight: Float,
//   cost: Integer,
//   description: String,
//   properties: Map (nullable)
// })

// Feature Node Structure:
// (:Feature {
//   name: String,
//   description: String,
//   source_type: String,
//   level_obtained: Integer (nullable),
//   prerequisites: Map (nullable)
// })

// Party Node Structure:
// (:Party {
//   name: String (unique),
//   created_at: DateTime,
//   description: String (nullable)
// })

// Campaign Node Structure:
// (:Campaign {
//   name: String (unique),
//   setting: String (nullable),
//   created_at: DateTime
// })

// ============================================================================
// RELATIONSHIP TYPES
// ============================================================================

// Character Relationships:
// (:Character)-[:HAS_CLASS {level: Integer}]->(:Class)
// (:Character)-[:HAS_SUBCLASS]->(:Subclass)
// (:Character)-[:HAS_RACE]->(:Race)
// (:Character)-[:HAS_BACKGROUND]->(:Background)
// (:Character)-[:OWNS {equipped: Boolean, quantity: Integer}]->(:Item)
// (:Character)-[:KNOWS_SPELL {prepared: Boolean, source: String}]->(:Spell)
// (:Character)-[:HAS_FEATURE]->(:Feature)
// (:Character)-[:HAS_FEAT]->(:Feat)
// (:Character)-[:BELONGS_TO_PARTY]->(:Party)

// Game System Relationships:
// (:Class)-[:GRANTS_FEATURE {level: Integer}]->(:Feature)
// (:Subclass)-[:GRANTS_FEATURE {level: Integer}]->(:Feature)
// (:Race)-[:GRANTS_FEATURE]->(:Feature)
// (:Background)-[:GRANTS_FEATURE]->(:Feature)
// (:Class)-[:CAN_LEARN_SPELL]->(:Spell)
// (:Spell)-[:REQUIRES_CLASS]->(:Class)
// (:Item)-[:REQUIRES_ATTUNEMENT]->(:Character)

// Campaign Relationships:
// (:Party)-[:HAS_CAMPAIGN]->(:Campaign)



