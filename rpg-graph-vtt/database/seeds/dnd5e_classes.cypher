// D&D 5e Core Classes Seed Data
// This script populates the graph with core character classes

// Fighter
CREATE (f:Fighter:Class {
    name: "Fighter",
    hit_die: 10,
    primary_ability: "STR",
    saving_throw_proficiencies: ["STR", "CON"],
    skill_proficiencies_count: 2,
    available_skills: ["Acrobatics", "Animal Handling", "Athletics", "History", "Insight", "Intimidation", "Perception", "Survival"],
    spellcasting_ability: null,
    subclasses: ["Champion", "Battle Master", "Eldritch Knight"]
});

// Wizard
CREATE (w:Wizard:Class {
    name: "Wizard",
    hit_die: 6,
    primary_ability: "INT",
    saving_throw_proficiencies: ["INT", "WIS"],
    skill_proficiencies_count: 2,
    available_skills: ["Arcana", "History", "Insight", "Investigation", "Medicine", "Religion"],
    spellcasting_ability: "INT",
    subclasses: ["Abjuration", "Conjuration", "Divination", "Enchantment", "Evocation", "Illusion", "Necromancy", "Transmutation"]
});

// Rogue
CREATE (r:Rogue:Class {
    name: "Rogue",
    hit_die: 8,
    primary_ability: "DEX",
    saving_throw_proficiencies: ["DEX", "INT"],
    skill_proficiencies_count: 4,
    available_skills: ["Acrobatics", "Athletics", "Deception", "Insight", "Intimidation", "Investigation", "Perception", "Performance", "Persuasion", "Sleight of Hand", "Stealth"],
    spellcasting_ability: null,
    subclasses: ["Thief", "Assassin", "Arcane Trickster"]
});

// Cleric
CREATE (c:Cleric:Class {
    name: "Cleric",
    hit_die: 8,
    primary_ability: "WIS",
    saving_throw_proficiencies: ["WIS", "CHA"],
    skill_proficiencies_count: 2,
    available_skills: ["History", "Insight", "Medicine", "Persuasion", "Religion"],
    spellcasting_ability: "WIS",
    subclasses: ["Life", "Light", "Nature", "Tempest", "Trickery", "War", "Knowledge"]
});

// Ranger
CREATE (ra:Ranger:Class {
    name: "Ranger",
    hit_die: 10,
    primary_ability: "DEX",
    saving_throw_proficiencies: ["STR", "DEX"],
    skill_proficiencies_count: 3,
    available_skills: ["Animal Handling", "Athletics", "Insight", "Investigation", "Nature", "Perception", "Stealth", "Survival"],
    spellcasting_ability: "WIS",
    subclasses: ["Beast Master", "Hunter", "Gloom Stalker"]
});

// Paladin
CREATE (p:Paladin:Class {
    name: "Paladin",
    hit_die: 10,
    primary_ability: "STR",
    saving_throw_proficiencies: ["WIS", "CHA"],
    skill_proficiencies_count: 2,
    available_skills: ["Athletics", "Insight", "Intimidation", "Medicine", "Persuasion", "Religion"],
    spellcasting_ability: "CHA",
    subclasses: ["Devotion", "Ancients", "Vengeance", "Conquest"]
});

// Barbarian
CREATE (b:Barbarian:Class {
    name: "Barbarian",
    hit_die: 12,
    primary_ability: "STR",
    saving_throw_proficiencies: ["STR", "CON"],
    skill_proficiencies_count: 2,
    available_skills: ["Animal Handling", "Athletics", "Intimidation", "Nature", "Perception", "Survival"],
    spellcasting_ability: null,
    subclasses: ["Berserker", "Totem Warrior", "Ancestral Guardian"]
});

// Bard
CREATE (ba:Bard:Class {
    name: "Bard",
    hit_die: 8,
    primary_ability: "CHA",
    saving_throw_proficiencies: ["DEX", "CHA"],
    skill_proficiencies_count: 3,
    available_skills: ["Athletics", "Acrobatics", "Sleight of Hand", "Stealth", "Arcana", "History", "Investigation", "Nature", "Religion", "Animal Handling", "Insight", "Medicine", "Perception", "Survival", "Deception", "Intimidation", "Performance", "Persuasion"],
    spellcasting_ability: "CHA",
    subclasses: ["Lore", "Valor", "Glamour"]
});

// Sorcerer
CREATE (s:Sorcerer:Class {
    name: "Sorcerer",
    hit_die: 6,
    primary_ability: "CHA",
    saving_throw_proficiencies: ["CON", "CHA"],
    skill_proficiencies_count: 2,
    available_skills: ["Arcana", "Deception", "Insight", "Intimidation", "Persuasion", "Religion"],
    spellcasting_ability: "CHA",
    subclasses: ["Draconic Bloodline", "Wild Magic", "Divine Soul"]
});

// Warlock
CREATE (wa:Warlock:Class {
    name: "Warlock",
    hit_die: 8,
    primary_ability: "CHA",
    saving_throw_proficiencies: ["WIS", "CHA"],
    skill_proficiencies_count: 2,
    available_skills: ["Arcana", "Deception", "History", "Intimidation", "Investigation", "Nature", "Religion"],
    spellcasting_ability: "CHA",
    subclasses: ["Fiend", "Great Old One", "Archfey", "Celestial"]
});

// Monk
CREATE (m:Monk:Class {
    name: "Monk",
    hit_die: 8,
    primary_ability: "DEX",
    saving_throw_proficiencies: ["STR", "DEX"],
    skill_proficiencies_count: 2,
    available_skills: ["Acrobatics", "Athletics", "History", "Insight", "Religion", "Stealth"],
    spellcasting_ability: null,
    subclasses: ["Open Hand", "Shadow", "Four Elements", "Drunken Master"]
});

// Druid
CREATE (d:Druid:Class {
    name: "Druid",
    hit_die: 8,
    primary_ability: "WIS",
    saving_throw_proficiencies: ["INT", "WIS"],
    skill_proficiencies_count: 2,
    available_skills: ["Arcana", "Animal Handling", "Insight", "Medicine", "Nature", "Perception", "Religion", "Survival"],
    spellcasting_ability: "WIS",
    subclasses: ["Land", "Moon", "Stars", "Wildfire"]
});

