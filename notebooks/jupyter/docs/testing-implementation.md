# Testing Implementation Guide

## Quick Start

### 1. Install Test Dependencies

```bash
pip install -r tests/requirements.txt
```

### 2. Set Up Test Environment

Create `.env.test`:
```env
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=test_password
```

### 3. Run Tests

```bash
# Unit tests
pytest tests/unit/ -v

# Integration tests
pytest tests/integration/ -v

# E2E tests (requires browser)
pytest tests/e2e/ -v
```

## Test Structure

```
tests/
├── unit/              # Unit tests
│   ├── test_adapters.py
│   ├── test_storage.py
│   └── test_services.py
├── integration/       # Integration tests
│   ├── test_neo4j_operations.py
│   └── test_workflows.py
└── e2e/              # End-to-end tests
    ├── puppeteer_test_setup.py
    ├── test_ecommerce_workflow.py
    └── conftest.py
```

## Puppeteer E2E Tests

### Basic Test Structure

```python
import pytest
from tests.e2e.puppeteer_test_setup import PuppeteerTestBase

@pytest.mark.asyncio
async def test_example(puppeteer):
    await puppeteer.navigate("https://example.com")
    await puppeteer.wait_for_selector("h1")
    text = await puppeteer.get_text("h1")
    assert "Example" in text
```

### GraphQL API Testing

```python
from tests.e2e.puppeteer_test_setup import GraphQLTestClient

@pytest.mark.asyncio
async def test_graphql_query(graphql_client):
    query = """
    query {
        products(limit: 10) {
            id
            title
            price
        }
    }
    """
    response = await graphql_client.query(query)
    assert "data" in response
    assert len(response["data"]["products"]) > 0
```

## Test Scenarios

### Scenario 1: Depop Product Crawl

1. Navigate to Depop product page
2. Wait for page load
3. Extract product data
4. Store in Neo4j
5. Verify via GraphQL

### Scenario 2: Shopify Product Crawl

1. Navigate to Shopify product page
2. Extract product data (including variants)
3. Store in Neo4j
4. Verify price history created

### Scenario 3: Garment Style Detection

1. Analyze image (mock CV input)
2. Create garment style
3. Match to products
4. Verify GraphQL queries work

### Scenario 4: Price Tracking

1. Store product with initial price
2. Update price
3. Verify price history
4. Query via GraphQL

## Continuous Integration

Tests should run in CI/CD pipeline:

```yaml
# .github/workflows/tests.yml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r tests/requirements.txt
      - name: Run tests
        run: pytest tests/ -v --cov=src/feed
        env:
          NEO4J_URI: ${{ secrets.TEST_NEO4J_URI }}
          NEO4J_PASSWORD: ${{ secrets.TEST_NEO4J_PASSWORD }}
```

## Debugging Tests

### View Browser
```python
base = PuppeteerTestBase(headless=False)
```

### Take Screenshots
```python
await puppeteer.screenshot("debug.png")
```

### Slow Down Actions
```python
base = PuppeteerTestBase(slow_mo=100)  # 100ms delay
```

### Network Logging
```python
page.on('request', lambda req: print(f"Request: {req.url}"))
page.on('response', lambda res: print(f"Response: {res.url} {res.status}"))
```



