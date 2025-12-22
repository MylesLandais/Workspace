// D&D 5e Core Backgrounds Seed Data
// This script populates the graph with core character backgrounds

// Acolyte
CREATE (a:Acolyte:Background {
    name: "Acolyte",
    skill_proficiencies: ["Insight", "Religion"],
    tool_proficiencies: [],
    languages: ["Two of your choice"],
    equipment: ["A holy symbol", "A prayer book or prayer wheel", "5 sticks of incense", "Vestments", "A set of common clothes", "A belt pouch containing 15 gp"]
});

// Criminal
CREATE (c:Criminal:Background {
    name: "Criminal",
    skill_proficiencies: ["Deception", "Stealth"],
    tool_proficiencies: ["One type of gaming set", "Thieves' tools"],
    languages: [],
    equipment: ["A crowbar", "A set of dark common clothes including a hood", "A belt pouch containing 15 gp"]
});

// Folk Hero
CREATE (fh:FolkHero:Background {
    name: "Folk Hero",
    skill_proficiencies: ["Animal Handling", "Survival"],
    tool_proficiencies: ["One type of artisan's tools", "Vehicles (land)"],
    languages: [],
    equipment: ["A set of artisan's tools", "A shovel", "An iron pot", "A set of common clothes", "A belt pouch containing 10 gp"]
});

// Noble
CREATE (n:Noble:Background {
    name: "Noble",
    skill_proficiencies: ["History", "Persuasion"],
    tool_proficiencies: ["One type of gaming set"],
    languages: ["One of your choice"],
    equipment: ["A set of fine clothes", "A signet ring", "A scroll of pedigree", "A purse containing 25 gp"]
});

// Sage
CREATE (s:Sage:Background {
    name: "Sage",
    skill_proficiencies: ["Arcana", "History"],
    tool_proficiencies: [],
    languages: ["Two of your choice"],
    equipment: ["A bottle of black ink", "A quill", "A small knife", "A letter from a dead colleague", "A set of common clothes", "A belt pouch containing 10 gp"]
});

// Soldier
CREATE (so:Soldier:Background {
    name: "Soldier",
    skill_proficiencies: ["Athletics", "Intimidation"],
    tool_proficiencies: ["One type of gaming set", "Vehicles (land)"],
    languages: ["One of your choice"],
    equipment: ["An insignia of rank", "A trophy taken from a fallen enemy", "A set of bone dice or deck of cards", "A set of common clothes", "A belt pouch containing 10 gp"]
});

// Hermit
CREATE (he:Hermit:Background {
    name: "Hermit",
    skill_proficiencies: ["Medicine", "Religion"],
    tool_proficiencies: ["Herbalism kit"],
    languages: ["One of your choice"],
    equipment: ["A scroll case stuffed full of notes", "A winter blanket", "A set of common clothes", "An herbalism kit", "5 gp"]
});

// Outlander
CREATE (ou:Outlander:Background {
    name: "Outlander",
    skill_proficiencies: ["Athletics", "Survival"],
    tool_proficiencies: ["One type of musical instrument"],
    languages: ["One of your choice"],
    equipment: ["A staff", "A hunting trap", "A trophy from an animal you killed", "A set of traveler's clothes", "A belt pouch containing 10 gp"]
});

// Entertainer
CREATE (en:Entertainer:Background {
    name: "Entertainer",
    skill_proficiencies: ["Acrobatics", "Performance"],
    tool_proficiencies: ["Disguise kit", "One type of musical instrument"],
    languages: [],
    equipment: ["A musical instrument", "The favor of an admirer", "A costume", "A belt pouch containing 15 gp"]
});

// Guild Artisan
CREATE (ga:GuildArtisan:Background {
    name: "Guild Artisan",
    skill_proficiencies: ["Insight", "Persuasion"],
    tool_proficiencies: ["One type of artisan's tools"],
    languages: ["One of your choice"],
    equipment: ["A set of artisan's tools", "A letter of introduction from your guild", "A set of traveler's clothes", "A belt pouch containing 15 gp"]
});

// Charlatan
CREATE (ch:Charlatan:Background {
    name: "Charlatan",
    skill_proficiencies: ["Deception", "Sleight of Hand"],
    tool_proficiencies: ["Disguise kit", "Forgery kit"],
    languages: [],
    equipment: ["A set of fine clothes", "A disguise kit", "Tools of the con of your choice", "A belt pouch containing 15 gp"]
});

// Sailor
CREATE (sa:Sailor:Background {
    name: "Sailor",
    skill_proficiencies: ["Athletics", "Perception"],
    tool_proficiencies: ["Navigator's tools", "Vehicles (water)"],
    languages: [],
    equipment: ["A belaying pin", "50 feet of silk rope", "A lucky charm", "A set of common clothes", "A belt pouch containing 10 gp"]
});



