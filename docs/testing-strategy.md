# Testing Strategy

## Overview

This document outlines the testing strategy for the e-commerce product tracking and garment style detection system, including unit tests, integration tests, and end-to-end Puppeteer tests.

## Testing Pyramid

```
        /\
       /E2E\        <- End-to-End Tests (Puppeteer)
      /------\
     /Integration\  <- Integration Tests
    /------------\
   /   Unit Tests  \ <- Unit Tests
  /----------------\
```

## Test Categories

### 1. Unit Tests

**Location**: `tests/unit/`

**Coverage**:
- Platform adapters (DepopAdapter, ShopifyAdapter, RedditAdapter)
- Storage operations (ProductStorage, thread_storage)
- Service logic (GarmentMatcher)
- Model validation (Product, Post, etc.)

**Example**:
```python
def test_depop_product_extraction():
    adapter = DepopAdapter(mock=True)
    product = adapter.fetch_product("https://depop.com/products/test/")
    assert product.title is not None
    assert product.price > 0
```

### 2. Integration Tests

**Location**: `tests/integration/`

**Coverage**:
- Neo4j operations
- End-to-end storage workflows
- Cross-component interactions
- Graph relationship creation

**Example**:
```python
def test_product_storage_with_price_history():
    neo4j = get_connection()
    storage = ProductStorage(neo4j)
    product = create_test_product()
    success = storage.store_product(product)
    assert success
    history = storage.get_price_history(product.id)
    assert len(history) > 0
```

### 3. End-to-End Tests (Puppeteer)

**Location**: `tests/e2e/`

**Coverage**:
- Full user workflows
- Real browser interactions
- GraphQL API testing
- Cross-platform product crawling
- Garment style detection workflow

**Requirements**:
- `pyppeteer` or `playwright` for browser automation
- Test server running (GraphQL API)
- Test database (separate Neo4j instance)

## Puppeteer E2E Test Setup

### Installation

```bash
pip install pyppeteer pytest pytest-asyncio
# Or use playwright:
pip install playwright pytest-playwright
playwright install chromium
```

### Test Structure

```python
@pytest.mark.asyncio
async def test_depop_product_crawl(puppeteer):
    """Test crawling Depop product page."""
    await puppeteer.navigate("https://depop.com/products/...")
    await puppeteer.wait_for_selector('[data-testid="product-title"]')
    # Verify page loaded correctly
    title = await puppeteer.get_text('h1')
    assert "yoga pants" in title.lower()
```

### Test Scenarios

#### E2E-001: Depop Product Crawl
- Navigate to Depop product page
- Verify page loads
- Extract product data
- Store in Neo4j
- Verify via GraphQL query

#### E2E-002: Shopify Product Crawl
- Navigate to Shopify product page
- Extract product data
- Store in Neo4j
- Verify price history created

#### E2E-003: Reddit Post with Images
- Navigate to Reddit post
- Extract images
- Store post and images
- Verify image relationships

#### E2E-004: Garment Style Detection
- Upload/analyze image
- Create garment style
- Match to products
- Verify GraphQL queries

#### E2E-005: Price Tracking
- Track product price
- Simulate price change
- Verify price history updated
- Query via GraphQL

#### E2E-006: GraphQL API
- Test all product queries
- Test garment style queries
- Test mutations (if any)
- Verify error handling

## GraphQL Schema Testing

### Schema Validation

Test that GraphQL schema is valid and accessible:

```python
async def test_graphql_schema_introspection(graphql_client):
    """Test GraphQL schema introspection."""
    query = """
    query IntrospectionQuery {
        __schema {
            types {
                name
                kind
            }
        }
    }
    """
    response = await graphql_client.query(query)
    assert "data" in response
    assert "__schema" in response["data"]
```

### Query Testing

Test all GraphQL queries:

```python
async def test_product_queries(graphql_client):
    """Test all product-related queries."""
    # Test product by ID
    # Test product search
    # Test product filtering
    # Test price history
```

### Mutation Testing

Test GraphQL mutations (when implemented):

```python
async def test_product_mutations(graphql_client):
    """Test product mutations."""
    # Test add product to tracking
    # Test update product
    # Test delete product
```

## Test Data Management

### Fixtures

Create reusable test fixtures:

```python
@pytest.fixture
def test_product():
    """Create test product."""
    return Product(
        id="test_product_1",
        title="Test Yoga Pants",
        price=25.00,
        currency="USD",
        # ...
    )

@pytest.fixture
def test_neo4j():
    """Get test Neo4j connection."""
    return get_connection(env_path=Path(".env.test"))
```

### Test Database

- Use separate Neo4j database for testing
- Clean up after each test
- Use transactions for rollback

### Mock Data

- Mock external APIs (Reddit, Depop, etc.)
- Use `mock=True` flag in adapters
- Create test fixtures for common scenarios

## Continuous Integration

### GitHub Actions / CI Pipeline

```yaml
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
          pip install pytest pytest-asyncio pyppeteer
      - name: Run unit tests
        run: pytest tests/unit/ -v
      - name: Run integration tests
        run: pytest tests/integration/ -v
      - name: Run E2E tests
        run: pytest tests/e2e/ -v
        env:
          NEO4J_URI: ${{ secrets.TEST_NEO4J_URI }}
          NEO4J_PASSWORD: ${{ secrets.TEST_NEO4J_PASSWORD }}
```

## Performance Testing

### Load Testing

- Test GraphQL query performance
- Test concurrent product crawls
- Test database query performance

### Benchmark Tests

- Garment style detection benchmark
- Product matching accuracy
- Price tracking latency

## Test Coverage Goals

- **Unit Tests**: 80%+ coverage
- **Integration Tests**: Critical paths covered
- **E2E Tests**: All user workflows covered
- **GraphQL Tests**: All queries and mutations tested

## Running Tests

### Unit Tests
```bash
pytest tests/unit/ -v
```

### Integration Tests
```bash
pytest tests/integration/ -v
```

### E2E Tests
```bash
pytest tests/e2e/ -v --headless
```

### All Tests
```bash
pytest tests/ -v
```

### With Coverage
```bash
pytest tests/ --cov=src/feed --cov-report=html
```

## Test Maintenance

### Regular Updates
- Update tests when schema changes
- Add tests for new features
- Remove obsolete tests

### Test Documentation
- Document test scenarios
- Explain test data requirements
- Document test environment setup

## Known Issues

- Puppeteer requires Chrome/Chromium installation
- E2E tests are slower than unit tests
- Need test database separate from production
- Rate limiting may affect E2E tests



