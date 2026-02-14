# End-to-End Tests

## Setup

### Install Dependencies

```bash
pip install -r tests/requirements.txt
```

### Install Browser

For Puppeteer (pyppeteer):
```bash
# Chrome/Chromium will be downloaded automatically on first run
```

For Playwright (alternative):
```bash
playwright install chromium
```

### Environment Setup

Create `.env.test` with test database credentials:

```env
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=test_password
```

## Running Tests

### All E2E Tests
```bash
pytest tests/e2e/ -v
```

### Specific Test
```bash
pytest tests/e2e/test_ecommerce_workflow.py::test_depop_product_crawl_and_store -v
```

### With Screenshots
```bash
pytest tests/e2e/ -v -s  # Keep screenshots
```

### Headless Mode (default)
Tests run in headless mode by default. To see browser:
```python
base = PuppeteerTestBase(headless=False)
```

## Test Structure

- `puppeteer_test_setup.py`: Base classes and utilities
- `test_ecommerce_workflow.py`: E2E test scenarios
- `conftest.py`: Pytest fixtures

## Test Scenarios

1. **Depop Product Crawl**: Navigate, extract, store
2. **Shopify Product Crawl**: Navigate, extract, store
3. **GraphQL Product Query**: Test API queries
4. **GraphQL Product Search**: Test search functionality
5. **Garment Style Detection**: Full CV workflow
6. **Price Tracking**: Verify price history updates

## Debugging

### View Browser
Set `headless=False` in test to see browser actions.

### Screenshots
Screenshots are saved automatically on failures.

### Slow Motion
```python
base = PuppeteerTestBase(headless=False, slow_mo=100)  # 100ms delay
```

### Network Logging
```python
await page.setRequestInterception(True)
page.on('request', lambda req: print(f"Request: {req.url}"))
```




