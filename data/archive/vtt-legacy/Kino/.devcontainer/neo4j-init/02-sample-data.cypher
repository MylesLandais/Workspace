// Sample Character Data for Testing
// This script creates sample D&D characters for user acceptance testing

// Sample Character 1: Human Fighter
MERGE (c1:Character {id: "sample-char-1"})
SET c1.name = "Aragorn",
    c1.level = 5,
    c1.str = 16,
    c1.dex = 14,
    c1.con = 15,
    c1.int = 12,
    c1.wis = 13,
    c1.cha = 10,
    c1.str_mod = 3,
    c1.dex_mod = 2,
    c1.con_mod = 2,
    c1.int_mod = 1,
    c1.wis_mod = 1,
    c1.cha_mod = 0,
    c1.proficiency_bonus = 3,
    c1.ac = 16,
    c1.max_hp = 45,
    c1.current_hp = 45,
    c1.race = "Human",
    c1.class = "Fighter",
    c1.background = "Folk Hero",
    c1.skills = "[]",
    c1.created_at = datetime(),
    c1.updated_at = datetime()

WITH c1
MERGE (r1:Race {name: "Human"})
ON CREATE SET r1.created_at = datetime()
MERGE (c1)-[:HAS_RACE]->(r1)

WITH c1
MERGE (cl1:Class {name: "Fighter"})
ON CREATE SET cl1.created_at = datetime()
MERGE (c1)-[:HAS_CLASS]->(cl1)

WITH c1
MERGE (b1:Background {name: "Folk Hero"})
ON CREATE SET b1.created_at = datetime()
MERGE (c1)-[:HAS_BACKGROUND]->(b1);

// Sample Character 2: Elf Wizard
MERGE (c2:Character {id: "sample-char-2"})
SET c2.name = "Gandalf",
    c2.level = 8,
    c2.str = 10,
    c2.dex = 13,
    c2.con = 14,
    c2.int = 18,
    c2.wis = 15,
    c2.cha = 12,
    c2.str_mod = 0,
    c2.dex_mod = 1,
    c2.con_mod = 2,
    c2.int_mod = 4,
    c2.wis_mod = 2,
    c2.cha_mod = 1,
    c2.proficiency_bonus = 3,
    c2.ac = 12,
    c2.max_hp = 52,
    c2.current_hp = 52,
    c2.race = "Elf",
    c2.class = "Wizard",
    c2.background = "Sage",
    c2.skills = "[]",
    c2.created_at = datetime(),
    c2.updated_at = datetime()

WITH c2
MERGE (r2:Race {name: "Elf"})
ON CREATE SET r2.created_at = datetime()
MERGE (c2)-[:HAS_RACE]->(r2)

WITH c2
MERGE (cl2:Class {name: "Wizard"})
ON CREATE SET cl2.created_at = datetime()
MERGE (c2)-[:HAS_CLASS]->(cl2)

WITH c2
MERGE (b2:Background {name: "Sage"})
ON CREATE SET b2.created_at = datetime()
MERGE (c2)-[:HAS_BACKGROUND]->(b2);

// Sample Character 3: Dwarf Cleric
MERGE (c3:Character {id: "sample-char-3"})
SET c3.name = "Thorin",
    c3.level = 3,
    c3.str = 14,
    c3.dex = 10,
    c3.con = 16,
    c3.int = 11,
    c3.wis = 17,
    c3.cha = 9,
    c3.str_mod = 2,
    c3.dex_mod = 0,
    c3.con_mod = 3,
    c3.int_mod = 0,
    c3.wis_mod = 3,
    c3.cha_mod = -1,
    c3.proficiency_bonus = 2,
    c3.ac = 18,
    c3.max_hp = 28,
    c3.current_hp = 28,
    c3.race = "Dwarf",
    c3.class = "Cleric",
    c3.background = "Acolyte",
    c3.skills = "[]",
    c3.created_at = datetime(),
    c3.updated_at = datetime()

WITH c3
MERGE (r3:Race {name: "Dwarf"})
ON CREATE SET r3.created_at = datetime()
MERGE (c3)-[:HAS_RACE]->(r3)

WITH c3
MERGE (cl3:Class {name: "Cleric"})
ON CREATE SET cl3.created_at = datetime()
MERGE (c3)-[:HAS_CLASS]->(cl3)

WITH c3
MERGE (b3:Background {name: "Acolyte"})
ON CREATE SET b3.created_at = datetime()
MERGE (c3)-[:HAS_BACKGROUND]->(b3);

