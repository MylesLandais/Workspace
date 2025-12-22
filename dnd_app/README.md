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
- `lib/dnd_app_web/` - Web layer
  - `live/` - LiveView pages
- `config/` - Configuration files

## D&D 5e Rules Implemented

- Ability score generation (4d6 drop lowest)
- Ability modifiers: (score - 10) / 2, rounded down
- Proficiency bonus: 2 + (level - 1) / 4, rounded up
- Starting HP: max hit die + CON modifier (level 1)
- Base AC: 10 + DEX modifier
- Race ability score bonuses

## License

MIT





