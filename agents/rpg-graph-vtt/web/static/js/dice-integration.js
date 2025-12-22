/**
 * Dice Integration - Character Sheet Click-to-Roll
 * 
 * Handles integration between character sheet and dice roller
 */

class DiceIntegration {
    constructor() {
        this.diceVisualizer = null;
        this.diceRoller = new DiceRoller();
        this.currentCharacter = null;
        this.modal = null;
    }

    /**
     * Initialize dice integration
     */
    init() {
        this.setupRollableElements();
        this.createModal();
    }

    /**
     * Create dice roller modal
     */
    createModal() {
        // Create modal HTML
        const modalHTML = `
            <div id="dice-modal" class="dice-modal" style="display: none;">
                <div class="dice-modal-content">
                    <div class="dice-modal-header">
                        <div class="dice-modal-title" id="dice-modal-title">Roll Dice</div>
                        <button class="dice-modal-close" onclick="diceIntegration.closeModal()">&times;</button>
                    </div>
                    <div class="dice-roller-container">
                        <div id="dice-tray-modal" class="dice-tray"></div>
                        <div class="dice-controls">
                            <div class="dice-control-group">
                                <label>Dice Notation</label>
                                <input type="text" id="modal-notation" class="notation-input" placeholder="e.g., 1d20+5" value="1d20">
                            </div>
                            <div class="dice-control-group">
                                <label>&nbsp;</label>
                                <button id="modal-roll-button" class="roll-button">Roll</button>
                            </div>
                        </div>
                        <div id="modal-results" class="dice-results hidden">
                            <div id="modal-results-content"></div>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Insert modal into body
        document.body.insertAdjacentHTML('beforeend', modalHTML);
        this.modal = document.getElementById('dice-modal');

        // Initialize dice visualizer in modal
        const tray = document.getElementById('dice-tray-modal');
        this.diceVisualizer = new DiceVisualizer(tray);

        // Setup modal event listeners
        this.setupModalListeners();

        // Close on background click
        this.modal.addEventListener('click', (e) => {
            if (e.target === this.modal) {
                this.closeModal();
            }
        });

        // Close on Escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.modal.style.display !== 'none') {
                this.closeModal();
            }
        });
    }

    /**
     * Setup modal event listeners
     */
    setupModalListeners() {
        const rollButton = document.getElementById('modal-roll-button');
        const notationInput = document.getElementById('modal-notation');

        rollButton.addEventListener('click', () => this.handleModalRoll());
        rollButton.addEventListener('touchstart', () => this.handleModalRoll()); // iOS support

        notationInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.handleModalRoll();
            }
        });

        // Listen for roll completion
        this.diceVisualizer.on('complete', (results) => {
            this.displayModalResults(results);
        });
    }

    /**
     * Handle roll from modal
     */
    handleModalRoll() {
        const notationInput = document.getElementById('modal-notation');
        const notation = notationInput.value.trim();

        if (!notation) {
            alert('Please enter dice notation (e.g., 1d20, 2d6+3)');
            return;
        }

        try {
            const result = this.diceRoller.roll(notation);
            const rollRequests = this.diceRoller.toVisualizerFormat(result);
            
            const rollButton = document.getElementById('modal-roll-button');
            rollButton.disabled = true;

            this.diceVisualizer.roll(rollRequests).then(() => {
                rollButton.disabled = false;
            });
        } catch (error) {
            alert(`Error: ${error.message}`);
        }
    }

    /**
     * Display results in modal
     */
    displayModalResults(results) {
        const resultsDiv = document.getElementById('modal-results');
        const contentDiv = document.getElementById('modal-results-content');

        resultsDiv.classList.remove('hidden');

        let html = '';
        let total = 0;

        results.forEach((result, index) => {
            total += result.faceValue;
            const isCritical = result.dieType === 'd20' && result.faceValue === 20;
            const isFail = result.dieType === 'd20' && result.faceValue === 1;

            html += `
                <div class="result-item">
                    <span class="result-label">Die ${index + 1} (${result.dieType}):</span>
                    <span class="result-value ${isCritical ? 'critical' : ''} ${isFail ? 'fail' : ''}">
                        ${result.faceValue}
                    </span>
                </div>
            `;
        });

        const modifier = results[0]?.modifier || 0;
        if (modifier !== 0) {
            total += modifier;
            html += `
                <div class="result-item">
                    <span class="result-label">Modifier:</span>
                    <span class="result-value">${modifier >= 0 ? '+' : ''}${modifier}</span>
                </div>
            `;
        }

        html += `
            <div class="result-total">
                Total: ${total}
            </div>
        `;

        contentDiv.innerHTML = html;
    }

    /**
     * Open dice modal with pre-filled notation
     */
    openModal(notation, label = 'Roll Dice') {
        const title = document.getElementById('dice-modal-title');
        title.textContent = label;

        const notationInput = document.getElementById('modal-notation');
        notationInput.value = notation;

        // Clear previous results
        const resultsDiv = document.getElementById('modal-results');
        resultsDiv.classList.add('hidden');

        // Clear dice tray
        if (this.diceVisualizer) {
            this.diceVisualizer.clearTray();
        }

        // Show modal
        this.modal.style.display = 'flex';
    }

    /**
     * Close dice modal
     */
    closeModal() {
        this.modal.style.display = 'none';
        if (this.diceVisualizer) {
            this.diceVisualizer.clearTray();
        }
    }

    /**
     * Setup rollable elements on character sheet
     */
    setupRollableElements() {
        // Use event delegation for dynamically added elements
        document.addEventListener('click', (e) => {
            const rollable = e.target.closest('.rollable');
            if (rollable) {
                e.preventDefault();
                this.handleRollableClick(rollable);
            }
        });

        // Also handle touch events for mobile
        document.addEventListener('touchstart', (e) => {
            const rollable = e.target.closest('.rollable');
            if (rollable) {
                e.preventDefault();
                this.handleRollableClick(rollable);
            }
        });
    }

    /**
     * Handle click on rollable element
     */
    handleRollableClick(element) {
        const rollNotation = element.dataset.roll;
        const label = element.dataset.label || 'Roll Dice';

        if (!rollNotation) {
            console.warn('Rollable element missing data-roll attribute');
            return;
        }

        // Replace character stat placeholders
        let notation = rollNotation;
        if (this.currentCharacter) {
            notation = this.replaceCharacterPlaceholders(notation, this.currentCharacter);
        }

        // Open modal with notation
        this.openModal(notation, label);
    }

    /**
     * Replace character stat placeholders in notation
     * Supports: @str.mod, @dex.mod, @con.mod, etc.
     */
    replaceCharacterPlaceholders(notation, character) {
        const abilityMap = {
            'str': character.ability_modifiers?.str || 0,
            'dex': character.ability_modifiers?.dex || 0,
            'con': character.ability_modifiers?.con || 0,
            'int': character.ability_modifiers?.int || 0,
            'wis': character.ability_modifiers?.wis || 0,
            'cha': character.ability_modifiers?.cha || 0
        };

        let result = notation;
        for (const [ability, modifier] of Object.entries(abilityMap)) {
            const placeholder = `@${ability}.mod`;
            const value = modifier >= 0 ? `+${modifier}` : `${modifier}`;
            result = result.replace(placeholder, value);
        }

        return result;
    }

    /**
     * Set current character context
     */
    setCharacter(character) {
        this.currentCharacter = character;
    }
}

// Create global instance
const diceIntegration = new DiceIntegration();

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        diceIntegration.init();
    });
} else {
    diceIntegration.init();
}



