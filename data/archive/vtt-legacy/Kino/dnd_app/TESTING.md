# Testing Guide

This document describes the test suite for the D&D App.

## Test Organization

```
test/
├── test_helper.exs          # Test configuration
├── support/                 # Test helpers
│   ├── conn_case.ex        # Connection test case
│   ├── live_case.ex        # LiveView test case
│   └── data_case.ex        # Data test case
├── dnd_app/                # Unit tests for core modules
│   ├── dice_test.exs       # Dice rolling tests
│   ├── characters_test.exs # Character logic tests
│   └── db/
│       └── neo4j_test.exs  # Database integration tests
└── dnd_app_web/            # Web layer tests
    └── live/
        ├── home_live_test.exs
        └── character_live_test.exs
```

## Test Types

### Unit Tests

Fast, isolated tests that don't require external dependencies.

**Examples:**
- `DndApp.DiceTest` - Tests dice rolling logic
- `DndApp.CharactersTest` - Tests stat calculations, modifiers, etc.

**Characteristics:**
- Run in parallel (`async: true`)
- No database required
- Fast execution

### Integration Tests

Tests that interact with Neo4j database.

**Examples:**
- `DndApp.DB.Neo4jTest` - Tests database CRUD operations

**Characteristics:**
- Tagged with `@moduletag :integration`
- Require running Neo4j instance
- May run sequentially

### LiveView Tests

Tests for Phoenix LiveView pages and user interactions.

**Examples:**
- `DndAppWeb.HomeLiveTest` - Tests dice roller UI
- `DndAppWeb.CharacterLiveTest` - Tests character creation flow

**Characteristics:**
- Use `DndAppWeb.LiveCase`
- Test user interactions
- Verify UI rendering

## Running Tests

### All Tests (Unit Only)

```bash
mix test
```

This excludes integration tests by default.

### All Tests Including Integration

```bash
mix test.all
# or
mix test --include integration
```

**Note:** Requires Neo4j running on `localhost:7687`

### Specific Test File

```bash
mix test test/dnd_app/dice_test.exs
```

### Specific Test

```bash
mix test test/dnd_app/dice_test.exs:15
```

### With Coverage

```bash
mix test --cover
```

## Test Coverage

Current test coverage includes:

### Dice Module (`DndApp.Dice`)
- ✅ Simple dice rolls (1d20, 4d6)
- ✅ Modifiers (+5, -3)
- ✅ Drop lowest/highest (4d6dl1, 2d20dh1)
- ✅ Error handling for invalid expressions
- ✅ Ability score generation

### Characters Module (`DndApp.Characters`)
- ✅ Ability modifier calculation
- ✅ Proficiency bonus calculation
- ✅ Race bonus application
- ✅ HP calculation
- ✅ AC calculation
- ✅ Race/class lookup

### Neo4j Module (`DndApp.DB.Neo4j`)
- ✅ Schema setup
- ✅ Character CRUD operations
- ✅ Relationship creation
- ✅ Error handling

### LiveView Pages
- ✅ Home page rendering
- ✅ Dice rolling UI
- ✅ Character creation flow
- ✅ Character list display
- ✅ Character sheet display

## CI/CD

Tests run automatically on:
- Push to `main` or `develop`
- Pull requests

See `.github/workflows/test.yml` for configuration.

## Test Data

Integration tests create test data in Neo4j. Tests should clean up after themselves using `on_exit` callbacks.

## Best Practices

1. **Test one thing per test**
2. **Use descriptive test names**
3. **Test edge cases and error conditions**
4. **Keep tests independent**
5. **Use `describe` blocks to group related tests**
6. **Mock external dependencies when possible**
7. **Clean up test data after tests**

## Troubleshooting

### Tests fail with Neo4j connection errors

Ensure Neo4j is running:
```bash
# Check if Neo4j is running
docker ps | grep neo4j

# Or start Neo4j
docker run -p 7687:7687 neo4j:5-community
```

### Integration tests fail

Make sure Neo4j is configured correctly in `config/test.exs` or via environment variables.

### LiveView tests timeout

Check that the Phoenix endpoint is configured correctly in test environment.





