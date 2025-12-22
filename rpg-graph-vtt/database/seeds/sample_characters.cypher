// Sample Characters for Testing and Demo
// These characters can be used to populate the database for development

// Create sample characters with relationships

// Character 1: Aragorn - Human Ranger
CREATE (c1:Character {
  uuid: "123e4567-e89b-12d3-a456-426614174000",
  name: "Aragorn",
  level: 10,
  hit_points: 85,
  hit_points_max: 85,
  armor_class: 18,
  proficiency_bonus: 4,
  ability_scores: {str: 18, dex: 16, con: 17, int: 14, wis: 15, cha: 13},
  ability_modifiers: {str: 4, dex: 3, con: 3, int: 2, wis: 2, cha: 1},
  saving_throws: {str: true, dex: false, con: true, int: false, wis: true, cha: false},
  skills: {athletics: true, perception: true, survival: true, stealth: true},
  created_at: datetime(),
  updated_at: datetime()
})
WITH c1
MATCH (r:Race {name: "Human"}), (bg:Background {name: "Folk Hero"})
CREATE (c1)-[:HAS_RACE]->(r)
CREATE (c1)-[:HAS_BACKGROUND]->(bg)
WITH c1
MATCH (cl:Class {name: "Ranger"})
CREATE (c1)-[:HAS_CLASS {level: 10}]->(cl);

// Character 2: Gandalf - Human Wizard
CREATE (c2:Character {
  uuid: "223e4567-e89b-12d3-a456-426614174001",
  name: "Gandalf",
  level: 15,
  hit_points: 120,
  hit_points_max: 120,
  armor_class: 15,
  proficiency_bonus: 5,
  ability_scores: {str: 10, dex: 12, con: 14, int: 20, wis: 18, cha: 16},
  ability_modifiers: {str: 0, dex: 1, con: 2, int: 5, wis: 4, cha: 3},
  saving_throws: {str: false, dex: false, con: true, int: true, wis: true, cha: true},
  skills: {arcana: true, history: true, investigation: true, religion: true},
  created_at: datetime(),
  updated_at: datetime()
})
WITH c2
MATCH (r:Race {name: "Human"}), (bg:Background {name: "Sage"})
CREATE (c2)-[:HAS_RACE]->(r)
CREATE (c2)-[:HAS_BACKGROUND]->(bg)
WITH c2
MATCH (cl:Class {name: "Wizard"})
CREATE (c2)-[:HAS_CLASS {level: 15}]->(cl);

// Character 3: Legolas - Elf Ranger
CREATE (c3:Character {
  uuid: "323e4567-e89b-12d3-a456-426614174002",
  name: "Legolas",
  level: 8,
  hit_points: 72,
  hit_points_max: 72,
  armor_class: 17,
  proficiency_bonus: 3,
  ability_scores: {str: 13, dex: 20, con: 14, int: 12, wis: 16, cha: 11},
  ability_modifiers: {str: 1, dex: 5, con: 2, int: 1, wis: 3, cha: 0},
  saving_throws: {str: false, dex: true, con: true, int: false, wis: false, cha: false},
  skills: {acrobatics: true, perception: true, stealth: true, survival: true},
  created_at: datetime(),
  updated_at: datetime()
})
WITH c3
MATCH (r:Race {name: "Elf"}), (bg:Background {name: "Outlander"})
CREATE (c3)-[:HAS_RACE]->(r)
CREATE (c3)-[:HAS_BACKGROUND]->(bg)
WITH c3
MATCH (cl:Class {name: "Ranger"})
CREATE (c3)-[:HAS_CLASS {level: 8}]->(cl);

// Character 4: Gimli - Dwarf Fighter
CREATE (c4:Character {
  uuid: "423e4567-e89b-12d3-a456-426614174003",
  name: "Gimli",
  level: 9,
  hit_points: 95,
  hit_points_max: 95,
  armor_class: 19,
  proficiency_bonus: 4,
  ability_scores: {str: 18, dex: 11, con: 18, int: 10, wis: 13, cha: 12},
  ability_modifiers: {str: 4, dex: 0, con: 4, int: 0, wis: 1, cha: 1},
  saving_throws: {str: true, dex: false, con: true, int: false, wis: false, cha: false},
  skills: {athletics: true, intimidation: true, perception: true},
  created_at: datetime(),
  updated_at: datetime()
})
WITH c4
MATCH (r:Race {name: "Dwarf"}), (bg:Background {name: "Soldier"})
CREATE (c4)-[:HAS_RACE]->(r)
CREATE (c4)-[:HAS_BACKGROUND]->(bg)
WITH c4
MATCH (cl:Class {name: "Fighter"})
CREATE (c4)-[:HAS_CLASS {level: 9}]->(cl);

// Character 5: Arwen - Elf Cleric
CREATE (c5:Character {
  uuid: "523e4567-e89b-12d3-a456-426614174004",
  name: "Arwen",
  level: 7,
  hit_points: 56,
  hit_points_max: 56,
  armor_class: 16,
  proficiency_bonus: 3,
  ability_scores: {str: 10, dex: 14, con: 13, int: 14, wis: 18, cha: 17},
  ability_modifiers: {str: 0, dex: 2, con: 1, int: 2, wis: 4, cha: 3},
  saving_throws: {str: false, dex: false, con: false, int: false, wis: true, cha: true},
  skills: {medicine: true, insight: true, religion: true, persuasion: true},
  created_at: datetime(),
  updated_at: datetime()
})
WITH c5
MATCH (r:Race {name: "Elf"}), (bg:Background {name: "Noble"})
CREATE (c5)-[:HAS_RACE]->(r)
CREATE (c5)-[:HAS_BACKGROUND]->(bg)
WITH c5
MATCH (cl:Class {name: "Cleric"})
CREATE (c5)-[:HAS_CLASS {level: 7}]->(cl);

// Create a sample party
CREATE (p1:Party {
  name: "Fellowship of the Ring",
  description: "A diverse group of heroes on an epic quest",
  created_at: datetime()
})
WITH p1
MATCH (c1:Character {name: "Aragorn"}), (c2:Character {name: "Gandalf"}), 
      (c3:Character {name: "Legolas"}), (c4:Character {name: "Gimli"}), 
      (c5:Character {name: "Arwen"})
CREATE (c1)-[:BELONGS_TO_PARTY]->(p1)
CREATE (c2)-[:BELONGS_TO_PARTY]->(p1)
CREATE (c3)-[:BELONGS_TO_PARTY]->(p1)
CREATE (c4)-[:BELONGS_TO_PARTY]->(p1)
CREATE (c5)-[:BELONGS_TO_PARTY]->(p1);



