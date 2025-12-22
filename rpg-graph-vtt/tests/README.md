# Testing Guide

This directory contains the test suite for RPG Graph VTT, organized following Google testing style.

## Structure

```
tests/
├── unit/                  # Unit tests (isolated, fast)
│   ├── test_models/      # Data model tests
│   ├── test_graph/       # Graph query tests
│   └── test_converters/  # Import/export converter tests
├── integration/          # Integration tests (require services)
│   ├── test_character_workflow.py
│   ├── test_party_management.py
│   └── test_api_endpoints.py
├── fixtures/             # Test fixtures and test data
│   ├── characters.py
│   ├── parties.py
│   └── neo4j.py
├── conftest.py           # Pytest configuration and shared fixtures
└── README.md
```

## Running Tests

### All Tests

```bash
pytest tests/
```

### Unit Tests Only

```bash
pytest tests/unit/
```

### Integration Tests Only

```bash
pytest tests/integration/ -m integration
```

### Specific Test File

```bash
pytest tests/unit/test_models/test_character.py
```

### With Coverage

```bash
pytest tests/ --cov=rpg_graph_vtt --cov-report=html
```

## Test Organization

### Unit Tests

Unit tests are fast, isolated, and mock external dependencies:
- **test_models/**: Test Pydantic model validation
- **test_graph/**: Test query builders with mocked Neo4j
- **test_converters/**: Test import/export logic

### Integration Tests

Integration tests require real services:
- **test_character_workflow.py**: Full character creation workflow
- **test_party_management.py**: Party operations with real Neo4j
- **test_api_endpoints.py**: FastAPI endpoint testing

**Note**: Integration tests are marked with `@pytest.mark.integration` and may be skipped if services aren't available.

## Test Fixtures

Shared test data and mocks are in `fixtures/`:
- **characters.py**: Sample character data
- **parties.py**: Sample party data
- **neo4j.py**: Neo4j connection fixtures

## Google Testing Style

Following Google's testing best practices:

1. **One test file per source file**: `test_character.py` tests `character.py`
2. **Test classes for grouping**: Related tests grouped in classes
3. **Descriptive test names**: `test_character_level_bounds()` not `test_level()`
4. **Fixtures for shared data**: Use `@pytest.fixture` for reusable test data
5. **Mock external dependencies**: Unit tests mock Neo4j, integration tests use real DB

## Example Test

```python
class TestCharacter:
    """Tests for Character model."""

    def test_create_character(self, sample_character_data):
        """Test creating a character with valid data."""
        char = Character(**sample_character_data)
        assert char.name == "Test Character"
```

## Continuous Integration

Tests should be run in CI/CD pipeline:
- Unit tests: Fast, always run
- Integration tests: May require test database setup

## Test Database

For integration tests, use a separate test Neo4j instance:
- Set `NEO4J_URI_TEST` environment variable
- Or create `.env.test` file with test database credentials
- Tests will clean the database before/after each test

