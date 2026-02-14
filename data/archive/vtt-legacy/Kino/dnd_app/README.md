# D&D 5e Character Creator

A Phoenix LiveView application for creating and managing D&D 5e characters with dice rolling capabilities.

## Features

- **Dice Rolling**: Roll dice with expressions like `1d20`, `4d6dl1` (drop lowest), `2d8+3`
- **Character Creation**: Step-by-step wizard for creating D&D 5e characters
  - Roll ability scores using 4d6 drop lowest method
  - Assign scores to abilities
  - Select race, class, and background
  - Automatic stat calculation (modifiers, AC, HP, proficiency bonus)
- **Character Management**: View, list, and delete characters
- **Neo4j Backend**: Stores characters in a graph database with relationships

## Requirements

- Elixir 1.14+
- Erlang/OTP 24+
- Neo4j database (running on localhost:7687 by default)
- Bun (for asset compilation and TypeScript) - [Install Bun](https://bun.sh/docs/installation)

**Recommended**: Use Docker Compose for the easiest setup. See [DOCKER_DEPLOYMENT.md](DOCKER_DEPLOYMENT.md) for complete Docker setup instructions.

## Quick Start

For detailed setup instructions, see **[DEV_SETUP.md](DEV_SETUP.md)**.

**Quick start:**
```bash
cd dnd_app
./start.sh
```

Then open http://localhost:4000 in your browser.

**Run diagnostics to check your setup:**
```bash
cd dnd_app
bin/check
```

## Setup

See **[DEV_SETUP.md](DEV_SETUP.md)** for complete setup instructions.

Quick setup:
1. Install dependencies: `mix deps.get && cd assets && bun install && cd ..`
2. Start Neo4j: `docker run -d --name neo4j-dnd -p 7474:7474 -p 7687:7687 -e NEO4J_AUTH=neo4j/password neo4j:5-community`
3. Start server: `./start.sh` or `mix phx.server`
4. Visit http://localhost:4000

**Docker Compose (Recommended)**:
```bash
docker-compose up
```
See [DOCKER_DEPLOYMENT.md](DOCKER_DEPLOYMENT.md) for detailed Docker setup.

## Usage

### Rolling Dice

- Enter dice expressions like:
  - `1d20` - roll a d20
  - `4d6dl1` - roll 4d6 and drop the lowest die
  - `2d8+3` - roll 2d8 and add 3
  - `1d20+5` - roll 1d20 and add 5

### Creating Characters

1. Go to "New Character"
2. Roll ability scores (6 sets of 4d6 drop lowest)
3. Assign scores to STR, DEX, CON, INT, WIS, CHA
4. Enter character details (name, race, class, background)
5. Review and create

The app automatically:
- Applies race ability score bonuses
- Calculates ability modifiers
- Calculates proficiency bonus based on level
- Calculates starting HP based on class and CON modifier
- Calculates AC (base 10 + DEX modifier)

## Project Structure

- `lib/dnd_app/` - Core application logic
  - `dice.ex` - Dice rolling engine
  - `characters.ex` - Character context and D&D 5e rules
  - `db/neo4j.ex` - Neo4j database operations
  - `risk_registry.ex` - Risk registry and dependency tracking system
- `lib/dnd_app_web/` - Web layer
  - `live/` - LiveView pages
- `config/` - Configuration files

## Risk Registry and Dependency Tracking

The project includes a comprehensive risk registry system for tracking technical dependencies, risks, constraints, and upstream triggers. This enables:

- **Dependency Tracking**: Document all technical dependencies (data sources, packages, services, infrastructure)
- **Risk Assessment**: Identify and track risks with severity levels
- **Upstream Triggers**: Monitor external data sources for changes
- **Version Tracking**: Track versions and changes in external dependencies
- **Supply Chain Visibility**: Understand dependency chains (bill of materials)

**Quick Start:**
```bash
# Register all dependencies
mix register.dependencies

# View in Neo4j Browser
# Open http://localhost:7474 and query: MATCH (d:Dependency) RETURN d
```

See [RISK_REGISTRY.md](RISK_REGISTRY.md) for complete documentation and [RISK_REGISTRY_QUICK_REFERENCE.md](RISK_REGISTRY_QUICK_REFERENCE.md) for quick reference.

## D&D 5e Rules Implemented

### Ability Score Generation

The app supports all three standard D&D 5e ability score generation methods:

1. **Rolling (4d6 drop lowest)**: Roll four six-sided dice, drop the lowest, sum the remaining three. Repeat six times. Produces scores from 3-18 (average ~12.24).

2. **Point Buy**: Start with 8 in all abilities, spend 27 points to increase scores. Costs: 8=0, 9=1, 10=2, 11=3, 12=4, 13=5, 14=7, 15=9. Maximum 15 before bonuses.

3. **Standard Array**: Use the fixed array [15, 14, 13, 12, 10, 8] assigned to abilities in any order.

**Note**: Your Dungeon Master decides which method(s) are allowed. Rolling creates randomness and potential imbalance, while Point Buy and Standard Array provide balanced characters.

### Ability Modifiers

Ability modifiers are calculated as: (score - 10) / 2, rounded down.

| Ability Score | Modifier |
|---------------|----------|
| 1             | -5       |
| 2-3           | -4       |
| 4-5           | -3       |
| 6-7           | -2       |
| 8-9           | -1       |
| 10-11         | +0       |
| 12-13         | +1       |
| 14-15         | +2       |
| 16-17         | +3       |
| 18-19         | +4       |
| 20+           | +5       |

### Other Rules

- Proficiency bonus: 2 + (level - 1) / 4, rounded up
- Starting HP: max hit die + CON modifier (level 1)
- Base AC: 10 + DEX modifier
- Race ability score bonuses (2014 PHB rules)

### 2024 Player's Handbook Updates

In the 2024 PHB, backgrounds now provide Ability Score Increases (ASI): +2/+1 or +1/+1/+1 from three options. Species provide feats and skills instead of ASI bonuses. This app currently implements the 2014 PHB rules where races/species provide ASI bonuses.

## License

MIT





