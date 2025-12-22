// D&D 5e Core Races Seed Data
// This script populates the graph with core character races

// Human
CREATE (h:Human:Race {
    name: "Human",
    ability_score_increases: {str: 1, dex: 1, con: 1, int: 1, wis: 1, cha: 1},
    size: "Medium",
    speed: 30,
    traits: ["Extra Language", "Extra Skill Proficiency"]
});

// Elf
CREATE (e:Elf:Race {
    name: "Elf",
    ability_score_increases: {dex: 2},
    size: "Medium",
    speed: 30,
    traits: ["Darkvision", "Keen Senses", "Fey Ancestry", "Trance"]
});

// High Elf (Subrace)
CREATE (he:HighElf:Race {
    name: "High Elf",
    ability_score_increases: {dex: 2, int: 1},
    size: "Medium",
    speed: 30,
    traits: ["Darkvision", "Keen Senses", "Fey Ancestry", "Trance", "Elf Weapon Training", "Cantrip", "Extra Language"]
});

// Wood Elf (Subrace)
CREATE (we:WoodElf:Race {
    name: "Wood Elf",
    ability_score_increases: {dex: 2, wis: 1},
    size: "Medium",
    speed: 35,
    traits: ["Darkvision", "Keen Senses", "Fey Ancestry", "Trance", "Elf Weapon Training", "Fleet of Foot", "Mask of the Wild"]
});

// Dwarf
CREATE (dw:Dwarf:Race {
    name: "Dwarf",
    ability_score_increases: {con: 2},
    size: "Medium",
    speed: 25,
    traits: ["Darkvision", "Dwarven Resilience", "Dwarven Combat Training", "Stonecunning"]
});

// Mountain Dwarf (Subrace)
CREATE (md:MountainDwarf:Race {
    name: "Mountain Dwarf",
    ability_score_increases: {con: 2, str: 2},
    size: "Medium",
    speed: 25,
    traits: ["Darkvision", "Dwarven Resilience", "Dwarven Combat Training", "Stonecunning", "Dwarven Armor Training"]
});

// Halfling
CREATE (ha:Halfling:Race {
    name: "Halfling",
    ability_score_increases: {dex: 2},
    size: "Small",
    speed: 25,
    traits: ["Lucky", "Brave", "Halfling Nimbleness"]
});

// Lightfoot Halfling (Subrace)
CREATE (lh:LightfootHalfling:Race {
    name: "Lightfoot Halfling",
    ability_score_increases: {dex: 2, cha: 1},
    size: "Small",
    speed: 25,
    traits: ["Lucky", "Brave", "Halfling Nimbleness", "Naturally Stealthy"]
});

// Dragonborn
CREATE (db:Dragonborn:Race {
    name: "Dragonborn",
    ability_score_increases: {str: 2, cha: 1},
    size: "Medium",
    speed: 30,
    traits: ["Draconic Ancestry", "Breath Weapon", "Damage Resistance"]
});

// Gnome
CREATE (g:Gnome:Race {
    name: "Gnome",
    ability_score_increases: {int: 2},
    size: "Small",
    speed: 25,
    traits: ["Darkvision", "Gnome Cunning"]
});

// Forest Gnome (Subrace)
CREATE (fg:ForestGnome:Race {
    name: "Forest Gnome",
    ability_score_increases: {int: 2, dex: 1},
    size: "Small",
    speed: 25,
    traits: ["Darkvision", "Gnome Cunning", "Natural Illusionist", "Speak with Small Beasts"]
});

// Tiefling
CREATE (t:Tiefling:Race {
    name: "Tiefling",
    ability_score_increases: {int: 1, cha: 2},
    size: "Medium",
    speed: 30,
    traits: ["Darkvision", "Hellish Resistance", "Infernal Legacy"]
});

// Half-Elf
CREATE (he2:HalfElf:Race {
    name: "Half-Elf",
    ability_score_increases: {cha: 2},
    size: "Medium",
    speed: 30,
    traits: ["Darkvision", "Fey Ancestry", "Skill Versatility"]
});

// Half-Orc
CREATE (ho:HalfOrc:Race {
    name: "Half-Orc",
    ability_score_increases: {str: 2, con: 1},
    size: "Medium",
    speed: 30,
    traits: ["Darkvision", "Menacing", "Relentless Endurance", "Savage Attacks"]
});



