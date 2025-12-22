# User Acceptance Testing Guide

This guide will help you preview and test the D&D 5e Character Creator application.

## Quick Start

### Prerequisites

1. **Elixir 1.14+** and **Erlang/OTP 24+** installed
2. **Node.js** (for asset compilation)
3. **Neo4j** database running (default: `localhost:7687`)

### Setup Steps

1. **Navigate to the project directory:**
   ```bash
   cd dnd_app
   ```

2. **Install Elixir dependencies:**
   ```bash
   mix deps.get
   ```

3. **Install Node.js dependencies:**
   ```bash
   cd assets && npm install && cd ..
   ```

4. **Start Neo4j** (if not already running):
   ```bash
   # Using Docker:
   docker run -d \
     --name neo4j \
     -p 7474:7474 -p 7687:7687 \
     -e NEO4J_AUTH=neo4j/password \
     neo4j:5-community
   
   # Or use your existing Neo4j installation
   ```

5. **Configure Neo4j connection** (if needed):
   Edit `config/config.exs` and update the Neo4j credentials:
   ```elixir
   config :bolt_sips, Bolt,
     url: "bolt://localhost:7687",
     basic_auth: [username: "neo4j", password: "your_password"],
   ```

6. **Start the Phoenix server:**
   ```bash
   mix phx.server
   ```

7. **Open your browser:**
   Navigate to: **http://localhost:4000**

## Application Features to Test

### 1. Home Page - Dice Roller (`/`)

**Test Cases:**
- [ ] Page loads and displays "D&D 5e Dice Roller" heading
- [ ] Dice expression input field is visible
- [ ] "Roll" button is clickable
- [ ] Quick roll buttons (d20, d12, d10, d8, d6, d4, 4d6) work
- [ ] Navigation links to Characters and New Character are visible

**Dice Rolling Tests:**
- [ ] Roll `1d20` - should show result between 1-20
- [ ] Roll `4d6` - should show 4 individual rolls and total
- [ ] Roll `4d6dl1` - should drop lowest die and show dropped value
- [ ] Roll `1d20+5` - should add modifier correctly
- [ ] Roll `2d8+3` - should handle multiple dice with modifier
- [ ] Invalid expression (e.g., "invalid") shows error message
- [ ] Result displays: total, individual rolls, dropped dice (if any), modifier

### 2. Character Creation (`/characters/new`)

**Step 1: Roll Ability Scores**
- [ ] "Roll Ability Scores" button is visible
- [ ] Clicking button generates 6 ability scores
- [ ] Scores are displayed as clickable buttons
- [ ] Clicking a score assigns it to the first available ability
- [ ] All 6 abilities (STR, DEX, CON, INT, WIS, CHA) can be assigned
- [ ] Assigned scores show with an "×" button to clear
- [ ] Clearing a score returns it to the available pool
- [ ] "Next: Character Details" button appears when all 6 scores are assigned
- [ ] Cannot proceed without assigning all scores

**Step 2: Character Details**
- [ ] Form displays: Name, Race, Class, Background
- [ ] Name field accepts text input
- [ ] Race dropdown shows all available races (Human, Elf, Dwarf, etc.)
- [ ] Class dropdown shows all available classes (Fighter, Wizard, etc.)
- [ ] Background dropdown shows all available backgrounds
- [ ] "Back" button returns to Step 1
- [ ] "Next: Review" button proceeds to Step 3
- [ ] Form updates in real-time as fields change

**Step 3: Review**
- [ ] Displays character name
- [ ] Shows selected race, class, and background
- [ ] Displays all 6 ability scores with modifiers
- [ ] Modifiers are calculated correctly (e.g., 15 STR = +2)
- [ ] "Back" button returns to Step 2
- [ ] "Create Character" button saves the character
- [ ] After creation, redirects to character sheet
- [ ] Error message if name is empty

### 3. Character List (`/characters`)

- [ ] Page displays "Characters" heading
- [ ] "Create New Character" button is visible
- [ ] If no characters exist, shows empty state message
- [ ] If characters exist, displays them in cards
- [ ] Each character card shows:
  - Character name
  - Level
  - Race
  - Class
  - "View" button
- [ ] Clicking "View" navigates to character sheet

### 4. Character Sheet (`/characters/:id`)

- [ ] Displays character name prominently
- [ ] Shows character metadata: Level, Race, Class, Background
- [ ] "Back to List" button works
- [ ] "Delete" button is visible
- [ ] Ability Scores section displays all 6 abilities:
  - STR, DEX, CON, INT, WIS, CHA
  - Each shows: score value and modifier
- [ ] Combat Stats section shows:
  - Armor Class (AC)
  - Hit Points (current/max)
  - Proficiency Bonus
- [ ] Character Information section shows:
  - Race, Class, Background, Level
- [ ] All calculated values are correct:
  - Modifiers match ability scores
  - AC = 10 + DEX modifier
  - HP matches class hit die + CON modifier
  - Proficiency bonus matches level

**Delete Functionality:**
- [ ] Clicking "Delete" removes the character
- [ ] Redirects to character list after deletion
- [ ] Character no longer appears in list

## Test Scenarios

### Scenario 1: Complete Character Creation Flow

1. Navigate to `/characters/new`
2. Roll ability scores
3. Assign scores: STR=16, DEX=14, CON=15, INT=10, WIS=12, CHA=8
4. Enter name: "Test Fighter"
5. Select: Race=Human, Class=Fighter, Background=Soldier
6. Review and verify all stats
7. Create character
8. Verify character sheet displays correctly
9. Verify character appears in list

### Scenario 2: Dice Rolling for Gameplay

1. Navigate to home page
2. Test various dice expressions:
   - `1d20` (attack roll)
   - `1d20+5` (attack with modifier)
   - `2d6+3` (damage roll)
   - `4d6dl1` (ability score)
3. Verify results are accurate
4. Test quick roll buttons

### Scenario 3: Multiple Characters

1. Create 3 different characters with different:
   - Races (Human, Elf, Dwarf)
   - Classes (Fighter, Wizard, Rogue)
   - Ability score distributions
2. Verify all appear in character list
3. View each character sheet
4. Verify stats are unique and correct for each

### Scenario 4: Race Bonuses

1. Create a Human character - verify +1 to all abilities
2. Create an Elf character - verify +2 DEX, +1 WIS
3. Create a Dwarf character - verify +2 CON, +1 STR
4. Verify final scores include bonuses

## Known Limitations (MVP)

- No inventory management
- No spell tracking
- No leveling system
- No multi-character party management
- No campaign management
- Simplified AC calculation (no armor)
- Skills list is stored but not fully implemented

## Browser Compatibility

Test in:
- [ ] Chrome/Edge (latest)
- [ ] Firefox (latest)
- [ ] Safari (latest)
- [ ] Mobile browsers (if applicable)

## Performance Testing

- [ ] Page loads quickly (< 2 seconds)
- [ ] Dice rolls are instant
- [ ] Character creation is responsive
- [ ] No lag when navigating between pages
- [ ] LiveView updates work smoothly

## Error Handling

- [ ] Invalid dice expressions show clear error messages
- [ ] Missing character name shows validation error
- [ ] Non-existent character ID redirects to list
- [ ] Neo4j connection errors are handled gracefully

## Accessibility

- [ ] All buttons are keyboard accessible
- [ ] Form fields have labels
- [ ] Error messages are visible
- [ ] Navigation is clear

## Reporting Issues

When reporting issues, include:
1. Browser and version
2. Steps to reproduce
3. Expected behavior
4. Actual behavior
5. Screenshots (if applicable)
6. Console errors (F12 → Console)

## Tips for Testing

1. **Use browser developer tools** (F12) to:
   - Check for JavaScript errors
   - Monitor network requests
   - Inspect LiveView socket connections

2. **Test edge cases:**
   - Very high/low ability scores
   - Special characters in names
   - Rapid clicking/button mashing

3. **Test data persistence:**
   - Create character, refresh page, verify it still exists
   - Create character, close browser, reopen, verify it's still there

4. **Test concurrent usage:**
   - Open multiple browser tabs
   - Create characters in different tabs
   - Verify all appear correctly





