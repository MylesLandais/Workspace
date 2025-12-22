# ComfyUI Agent Tests

Comprehensive test suite for the ComfyUI Image Generation Agent following ADK best practices.

## Test Structure

```
tests/
├── __init__.py              # Package initialization
├── conftest.py              # Pytest fixtures and configuration
├── test_prompts.py          # Prompt template validation
├── test_tools.py            # Tool unit tests with mocked RunPod
└── test_agent.py            # Integration tests with ADK Runner
```

## Running Tests

### Prerequisites

Install pytest and dependencies:

```bash
pip install pytest pytest-asyncio python-dotenv
```

Or in Docker:

```bash
docker exec jupyter pip install pytest pytest-asyncio
```

### Run All Tests

```bash
# From project root
pytest agents/comfy/tests/

# With verbose output
pytest agents/comfy/tests/ -v

# With coverage
pytest agents/comfy/tests/ --cov=agents.comfy
```

### Run Specific Test Categories

```bash
# Unit tests only (fast, no API calls)
pytest agents/comfy/tests/ -m unit

# Integration tests (slower, requires API keys)
pytest agents/comfy/tests/ -m integration

# Slow tests (optional in CI/CD)
pytest agents/comfy/tests/ -m "not slow"

# Tests requiring API keys (skip in CI/CD)
pytest agents/comfy/tests/ -m "not requires_api"
```

### Run Specific Test Files

```bash
# Prompt template tests
pytest agents/comfy/tests/test_prompts.py -v

# Tool tests with mocks
pytest agents/comfy/tests/test_tools.py -v

# Agent integration tests
pytest agents/comfy/tests/test_agent.py -v
```

## Test Categories

### Unit Tests (`test_prompts.py`, `test_tools.py`)

- **Fast**: No external API calls
- **Mocked**: RunPod responses are mocked
- **Purpose**: Validate individual components

Examples:
- Prompt templates don't contain unresolved `{variables}`
- Tools handle errors correctly
- Workflow loading works
- Parameter validation

### Integration Tests (`test_agent.py`)

- **Slower**: Full agent workflow
- **Real ADK**: Uses actual ADK Runner
- **Purpose**: Validate agent orchestration

Examples:
- Agent loads correctly
- Sub-agents can be invoked
- Full generation workflow (with API keys)

## Pytest Markers

Custom markers for test categorization:

- `@pytest.mark.unit` - Unit tests (fast, mocked)
- `@pytest.mark.integration` - Integration tests (slower)
- `@pytest.mark.slow` - Tests that take a long time
- `@pytest.mark.requires_api` - Tests requiring API keys

## Fixtures

Common fixtures from `conftest.py`:

- `test_workflow` - Minimal workflow structure for testing
- `mock_runpod_success` - Mock successful RunPod execution
- `mock_runpod_failure` - Mock failed RunPod execution
- `mock_runpod_timeout` - Mock timed out RunPod execution
- `session_service` - In-memory ADK session service
- `test_session` - Pre-configured test session
- `sample_prompts` - Collection of test prompts

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Test ComfyUI Agent

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-asyncio
      
      - name: Run unit tests
        run: pytest agents/comfy/tests/ -m unit -v
      
      - name: Run integration tests
        if: ${{ github.event_name == 'push' && github.ref == 'refs/heads/main' }}
        env:
          OPENROUTER_API_KEY: ${{ secrets.OPENROUTER_API_KEY }}
          RUNPOD_API_KEY: ${{ secrets.RUNPOD_API_KEY }}
        run: pytest agents/comfy/tests/ -m "integration and not slow" -v
```

## Test Coverage Goals

- **Prompt Templates**: 100% - All templates validated
- **Tools**: 80%+ - All major paths covered
- **Agent Integration**: Basic smoke tests

## Writing New Tests

### Test Naming Convention

```python
def test_<component>_<scenario>():
    """Test that <component> <expected behavior>."""
    # Arrange
    # Act
    # Assert
```

### Example Unit Test

```python
@pytest.mark.unit
def test_tool_validates_empty_prompt():
    """Test that generate_image_with_runpod rejects empty prompts."""
    result = generate_image_with_runpod(prompt="")
    assert result["status"] == "error"
    assert "empty" in result["message"].lower()
```

### Example Integration Test

```python
@pytest.mark.integration
async def test_agent_can_enhance_prompt(self):
    """Test that prompt enhancer sub-agent works."""
    response = self._run_agent(prompt_enhancer_agent, "A red apple")
    self.assertIsNotNone(response)
    self.assertGreater(len(response), 0)
```

## Debugging Tests

### Run with Debug Output

```bash
# Show print statements
pytest agents/comfy/tests/ -v -s

# Show local variables on failure
pytest agents/comfy/tests/ -v -l

# Drop into debugger on failure
pytest agents/comfy/tests/ --pdb
```

### Enable Comfy Debug Mode

```bash
export COMFY_DEBUG=1
pytest agents/comfy/tests/ -v -s
```

## Known Issues

1. **Pytest not installed**: Run `pip install pytest pytest-asyncio`
2. **Missing API keys**: Set `OPENROUTER_API_KEY` and `RUNPOD_API_KEY` in `.env`
3. **Import errors**: Ensure project root is in `PYTHONPATH` or run from project root

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [ADK Testing Patterns](https://github.com/google/adk/docs/testing.md)
- [Data Science Agent Tests](../data-science/tests/) - Reference implementation



