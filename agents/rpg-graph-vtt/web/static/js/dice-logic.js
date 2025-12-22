/**
 * Dice Logic - Notation Parser and RNG Wrapper
 * 
 * Parses dice notation (e.g., "2d6+3", "1d20+5") and generates roll results.
 * Can work with client-side RNG or server-authoritative results.
 * 
 * @class DiceRoller
 */
class DiceRoller {
    constructor(rng = null) {
        // Use provided RNG or default to Math.random
        this.rng = rng || (() => Math.random());
    }

    /**
     * Parse dice notation string
     * Supports: "1d20", "2d6+3", "1d20+5-2", "d20" (assumes 1 die)
     * @param {string} notation - Dice notation string
     * @returns {Object} Parsed notation object
     */
    parseNotation(notation) {
        const trimmed = notation.trim().toLowerCase();
        
        // Match pattern: [count]d[sides][+/-modifier]
        const match = trimmed.match(/^(\d*)d(\d+)([+-]\d+)?$/);
        
        if (!match) {
            throw new Error(`Invalid dice notation: ${notation}`);
        }

        const count = match[1] ? parseInt(match[1], 10) : 1;
        const sides = parseInt(match[2], 10);
        const modifier = match[3] ? parseInt(match[3], 10) : 0;

        if (count < 1 || count > 100) {
            throw new Error(`Die count must be between 1 and 100, got: ${count}`);
        }

        if (sides < 2 || sides > 100) {
            throw new Error(`Die sides must be between 2 and 100, got: ${sides}`);
        }

        return {
            count,
            sides,
            modifier,
            notation: trimmed
        };
    }

    /**
     * Roll a single die
     * @param {number} sides - Number of sides
     * @returns {number} Random result between 1 and sides
     */
    rollDie(sides) {
        return Math.floor(this.rng() * sides) + 1;
    }

    /**
     * Roll dice based on notation
     * @param {string} notation - Dice notation string
     * @returns {Object} Roll result with individual dice and total
     */
    roll(notation) {
        const parsed = this.parseNotation(notation);
        const rolls = [];

        for (let i = 0; i < parsed.count; i++) {
            rolls.push(this.rollDie(parsed.sides));
        }

        const sum = rolls.reduce((a, b) => a + b, 0);
        const total = sum + parsed.modifier;

        return {
            notation: parsed.notation,
            rolls: rolls,
            modifier: parsed.modifier,
            sum: sum,
            total: total,
            dieType: `d${parsed.sides}`,
            count: parsed.count
        };
    }

    /**
     * Roll with pre-determined results (for server-authoritative or testing)
     * @param {string} notation - Dice notation string
     * @param {Array<number>} faceValues - Pre-determined face values
     * @returns {Object} Roll result
     */
    rollWithResults(notation, faceValues) {
        const parsed = this.parseNotation(notation);
        
        if (faceValues.length !== parsed.count) {
            throw new Error(`Face values count (${faceValues.length}) must match die count (${parsed.count})`);
        }

        const sum = faceValues.reduce((a, b) => a + b, 0);
        const total = sum + parsed.modifier;

        return {
            notation: parsed.notation,
            rolls: faceValues,
            modifier: parsed.modifier,
            sum: sum,
            total: total,
            dieType: `d${parsed.sides}`,
            count: parsed.count
        };
    }

    /**
     * Convert roll result to DiceVisualizer format
     * @param {Object} rollResult - Result from roll() or rollWithResults()
     * @returns {Array} Array of roll requests for DiceVisualizer
     */
    toVisualizerFormat(rollResult) {
        return rollResult.rolls.map(faceValue => ({
            dieType: rollResult.dieType,
            faceValue: faceValue,
            modifier: rollResult.modifier / rollResult.count // Distribute modifier evenly (or could be per-die)
        }));
    }

    /**
     * Parse complex notation (future: support "2d6+1d8+3")
     * For MVP, we'll handle simple cases
     * @param {string} notation - Complex dice notation
     * @returns {Array} Array of parsed components
     */
    parseComplexNotation(notation) {
        // Simple implementation: split by + and parse each part
        const parts = notation.split(/\s*\+\s*/);
        const results = [];

        for (const part of parts) {
            if (part.match(/^\d+$/)) {
                // Pure modifier
                results.push({
                    type: 'modifier',
                    value: parseInt(part, 10)
                });
            } else if (part.match(/^\d*d\d+$/)) {
                // Dice notation
                const parsed = this.parseNotation(part);
                results.push({
                    type: 'dice',
                    ...parsed
                });
            } else {
                throw new Error(`Invalid notation part: ${part}`);
            }
        }

        return results;
    }

    /**
     * Roll complex notation
     * @param {string} notation - Complex dice notation like "2d6+1d8+3"
     * @returns {Object} Combined roll result
     */
    rollComplex(notation) {
        const components = this.parseComplexNotation(notation);
        const allRolls = [];
        let totalModifier = 0;

        for (const component of components) {
            if (component.type === 'modifier') {
                totalModifier += component.value;
            } else if (component.type === 'dice') {
                const result = this.roll(`${component.count}d${component.sides}`);
                allRolls.push(...result.rolls);
            }
        }

        const sum = allRolls.reduce((a, b) => a + b, 0);
        const total = sum + totalModifier;

        return {
            notation: notation,
            rolls: allRolls,
            modifier: totalModifier,
            sum: sum,
            total: total,
            components: components
        };
    }
}

/**
 * Utility function to convert standard die types to sides
 */
function dieTypeToSides(dieType) {
    const mapping = {
        'd4': 4,
        'd6': 6,
        'd8': 8,
        'd10': 10,
        'd12': 12,
        'd20': 20,
        'd100': 100
    };
    return mapping[dieType.toLowerCase()] || null;
}

/**
 * Utility function to get max value for die type
 */
function getMaxValue(dieType) {
    return dieTypeToSides(dieType) || 20;
}

// Export for use in modules or global scope
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { DiceRoller, dieTypeToSides, getMaxValue };
}



