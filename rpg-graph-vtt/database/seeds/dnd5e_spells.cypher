// D&D 5e Core Spells Seed Data (Sample - Full spell list would be extensive)
// This script populates the graph with a selection of core spells

// Cantrips (Level 0)
CREATE (fb:FireBolt:Spell {
    name: "Fire Bolt",
    level: 0,
    school: "Evocation",
    casting_time: "1 action",
    range: "120 feet",
    components: "V, S",
    material_components: null,
    duration: "Instantaneous",
    description: "You hurl a mote of fire at a creature or object within range. Make a ranged spell attack against the target. On a hit, the target takes 1d10 fire damage. A flammable object hit by this spell ignites if it isn't being worn or carried.",
    higher_levels: "This spell's damage increases by 1d10 when you reach 5th level (2d10), 11th level (3d10), and 17th level (4d10).",
    ritual: false,
    concentration: false
});

CREATE (mg:MageHand:Spell {
    name: "Mage Hand",
    level: 0,
    school: "Conjuration",
    casting_time: "1 action",
    range: "30 feet",
    components: "V, S",
    material_components: null,
    duration: "1 minute",
    description: "A spectral, floating hand appears at a point you choose within range. The hand lasts for the duration or until you dismiss it as an action. The hand vanishes if it is ever more than 30 feet away from you or if you cast this spell again.",
    higher_levels: null,
    ritual: false,
    concentration: false
});

CREATE (lb:Light:Spell {
    name: "Light",
    level: 0,
    school: "Evocation",
    casting_time: "1 action",
    range: "Touch",
    components: "V, M",
    material_components: "A firefly or phosphorescent moss",
    duration: "1 hour",
    description: "You touch one object that is no larger than 10 feet in any dimension. Until the spell ends, the object sheds bright light in a 20-foot radius and dim light for an additional 20 feet.",
    higher_levels: null,
    ritual: false,
    concentration: false
});

// 1st Level Spells
CREATE (ms:MagicMissile:Spell {
    name: "Magic Missile",
    level: 1,
    school: "Evocation",
    casting_time: "1 action",
    range: "120 feet",
    components: "V, S",
    material_components: null,
    duration: "Instantaneous",
    description: "You create three glowing darts of magical force. Each dart hits a creature of your choice that you can see within range. A dart deals 1d4 + 1 force damage to its target. The darts all strike simultaneously, and you can direct them to hit one creature or several.",
    higher_levels: "When you cast this spell using a spell slot of 2nd level or higher, the spell creates one more dart for each slot level above 1st.",
    ritual: false,
    concentration: false
});

CREATE (sh:Shield:Spell {
    name: "Shield",
    level: 1,
    school: "Abjuration",
    casting_time: "1 reaction",
    range: "Self",
    components: "V, S",
    material_components: null,
    duration: "1 round",
    description: "An invisible barrier of magical force appears and protects you. Until the start of your next turn, you have a +5 bonus to AC, including against the triggering attack, and you take no damage from magic missile.",
    higher_levels: null,
    ritual: false,
    concentration: false
});

CREATE (cu:CureWounds:Spell {
    name: "Cure Wounds",
    level: 1,
    school: "Evocation",
    casting_time: "1 action",
    range: "Touch",
    components: "V, S",
    material_components: null,
    duration: "Instantaneous",
    description: "A creature you touch regains a number of hit points equal to 1d8 + your spellcasting ability modifier. This spell has no effect on undead or constructs.",
    higher_levels: "When you cast this spell using a spell slot of 2nd level or higher, the healing increases by 1d8 for each slot level above 1st.",
    ritual: false,
    concentration: false
});

// 2nd Level Spells
CREATE (in:Invisibility:Spell {
    name: "Invisibility",
    level: 2,
    school: "Illusion",
    casting_time: "1 action",
    range: "Touch",
    components: "V, S, M",
    material_components: "An eyelash encased in gum arabic",
    duration: "1 hour",
    description: "A creature you touch becomes invisible until the spell ends. Anything the target is wearing or carrying is invisible as long as it is on the target's person. The spell ends for a target that attacks or casts a spell.",
    higher_levels: "When you cast this spell using a spell slot of 3rd level or higher, you can target one additional creature for each slot level above 2nd.",
    ritual: false,
    concentration: false
});

CREATE (fb2:Fireball:Spell {
    name: "Fireball",
    level: 3,
    school: "Evocation",
    casting_time: "1 action",
    range: "150 feet",
    components: "V, S, M",
    material_components: "A tiny ball of bat guano and sulfur",
    duration: "Instantaneous",
    description: "A bright streak flashes from your pointing finger to a point you choose within range and then blossoms with a low roar into an explosion of flame. Each creature in a 20-foot-radius sphere centered on that point must make a Dexterity saving throw. A target takes 8d6 fire damage on a failed save, or half as much damage on a successful one.",
    higher_levels: "When you cast this spell using a spell slot of 4th level or higher, the damage increases by 1d6 for each slot level above 3rd.",
    ritual: false,
    concentration: false
});

// Link spells to classes that can learn them
MATCH (w:Class {name: "Wizard"})
MATCH (s:Spell)
WHERE s.name IN ["Fire Bolt", "Mage Hand", "Light", "Magic Missile", "Shield", "Invisibility", "Fireball"]
MERGE (w)-[:CAN_LEARN_SPELL]->(s);

MATCH (c:Class {name: "Cleric"})
MATCH (s:Spell {name: "Cure Wounds"})
MERGE (c)-[:CAN_LEARN_SPELL]->(s);

MATCH (c:Class {name: "Cleric"})
MATCH (s:Spell {name: "Light"})
MERGE (c)-[:CAN_LEARN_SPELL]->(s);

