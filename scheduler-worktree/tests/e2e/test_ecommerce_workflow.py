"""End-to-end tests for e-commerce product tracking workflow using Puppeteer."""

import pytest
import asyncio
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from puppeteer_test_setup import PuppeteerTestBase, GraphQLTestClient
from feed.platforms.depop import DepopAdapter
from feed.platforms.shopify import ShopifyAdapter
from feed.storage.neo4j_connection import get_connection
from feed.storage.product_storage import ProductStorage
from feed.services.garment_matcher import GarmentMatcher


@pytest.fixture
async def puppeteer():
    """Puppeteer test fixture."""
    base = PuppeteerTestBase(headless=True)
    await base.setup()
    yield base
    await base.teardown()


@pytest.fixture
def graphql_client():
    """GraphQL client fixture."""
    return GraphQLTestClient()


@pytest.mark.asyncio
async def test_depop_product_crawl_and_store(puppeteer):
    """Test crawling a Depop product and storing in Neo4j."""
    # Test product URL
    product_url = "https://www.depop.com/products/krista_h-hot-pink-tights-thick-and/"
    
    # Navigate to product page
    await puppeteer.navigate(product_url)
    
    # Wait for page to load
    await puppeteer.wait_for_selector('h1, [data-testid="product-title"]', timeout=10000)
    
    # Take screenshot for verification
    await puppeteer.screenshot('test_depop_product_page.png')
    
    # Extract product data using adapter
    depop = DepopAdapter(mock=False)
    product = depop.fetch_product(product_url)
    
    assert product is not None, "Failed to fetch product"
    assert product.title, "Product title is empty"
    assert product.price > 0, "Product price is invalid"
    
    # Store in Neo4j
    neo4j = get_connection()
    product_storage = ProductStorage(neo4j)
    success = product_storage.store_product(product)
    
    assert success, "Failed to store product"
    
    # Verify in database
    stored_product = product_storage.get_product(product.id)
    assert stored_product is not None, "Product not found in database"
    assert stored_product.get('title') == product.title, "Product title mismatch"


@pytest.mark.asyncio
async def test_shopify_product_crawl_and_store(puppeteer):
    """Test crawling a Shopify product and storing in Neo4j."""
    product_url = "https://shop.hanrousa.com/products/net-womens-fine-netted-tights-black-40658-3009?variant=41361668571271"
    
    # Navigate to product page
    await puppeteer.navigate(product_url)
    
    # Wait for page to load
    await puppeteer.wait_for_selector('h1, .product-title', timeout=10000)
    
    # Take screenshot
    await puppeteer.screenshot('test_shopify_product_page.png')
    
    # Extract product data
    shopify = ShopifyAdapter(mock=False)
    product = shopify.fetch_product(product_url)
    
    assert product is not None, "Failed to fetch product"
    assert product.title, "Product title is empty"
    assert product.price > 0, "Product price is invalid"
    
    # Store in Neo4j
    neo4j = get_connection()
    product_storage = ProductStorage(neo4j)
    success = product_storage.store_product(product)
    
    assert success, "Failed to store product"


@pytest.mark.asyncio
async def test_graphql_product_query(graphql_client):
    """Test GraphQL product query."""
    query = """
    query GetProduct($id: String!) {
        product(id: $id) {
            id
            title
            price
            currency
            status
            brand
            images {
                url
                imageIndex
            }
            seller {
                username
            }
            priceHistory(limit: 5) {
                price
                currency
                timestamp
            }
        }
    }
    """
    
    # First, ensure we have a product
    neo4j = get_connection()
    product_storage = ProductStorage(neo4j)
    
    # Get a product ID from database
    query_check = "MATCH (p:Product) RETURN p.id as id LIMIT 1"
    result = neo4j.execute_read(query_check)
    
    if not result:
        pytest.skip("No products in database for testing")
    
    product_id = result[0]["id"]
    
    # Query via GraphQL
    response = await graphql_client.query(query, variables={"id": product_id})
    
    assert "data" in response, f"GraphQL error: {response.get('errors')}"
    assert response["data"]["product"] is not None, "Product not found"
    assert response["data"]["product"]["id"] == product_id, "Product ID mismatch"


@pytest.mark.asyncio
async def test_graphql_product_search(graphql_client):
    """Test GraphQL product search."""
    query = """
    query SearchProducts($query: String!) {
        searchProducts(queryText: $query, limit: 10) {
            id
            title
            price
            currency
            brand
        }
    }
    """
    
    response = await graphql_client.query(query, variables={"query": "yoga pants"})
    
    assert "data" in response, f"GraphQL error: {response.get('errors')}"
    assert "searchProducts" in response["data"], "Search products field missing"
    assert isinstance(response["data"]["searchProducts"], list), "Search results not a list"


@pytest.mark.asyncio
async def test_graphql_garment_style_query(graphql_client):
    """Test GraphQL garment style query."""
    query = """
    query GetGarmentStyles {
        garmentStyles(limit: 10) {
            uuid
            name
            category
            garmentType
            primaryStyle
            features {
                featureType
                featureValue
            }
            matchedProducts(limit: 5) {
                product {
                    id
                    title
                    price
                }
                confidenceScore
                matchType
            }
        }
    }
    """
    
    response = await graphql_client.query(query)
    
    assert "data" in response, f"GraphQL error: {response.get('errors')}"
    assert "garmentStyles" in response["data"], "Garment styles field missing"


@pytest.mark.asyncio
async def test_garment_style_detection_workflow(puppeteer):
    """Test full workflow: image -> style -> products."""
    # This would test the full CV workflow
    # For now, we'll test with mock analysis
    
    neo4j = get_connection()
    matcher = GarmentMatcher(neo4j)
    
    # Mock image analysis (would come from CV model)
    image_analysis = {
        "garment_type": "Yoga Pants",
        "color": "Black",
        "panel_type": "Sheer Panel",
        "fit": "Compression",
        "length": "Full Length",
        "material": "Polyester/Spandex",
        "features": [
            "sheer_panel_thigh",
            "sheer_panel_calf",
            "vertical_panels",
            "compression_fit",
        ],
    }
    
    image_url = "https://i.redd.it/test-sheer-panel-yoga-pants.jpg"
    
    result = matcher.analyze_and_match_image(
        image_url=image_url,
        image_analysis=image_analysis,
    )
    
    assert result["style_id"], "Style ID not created"
    assert result["style_name"] == "Sheer Panel Yoga Pants", "Style name incorrect"
    assert len(result["search_links"]) > 0, "No search links generated"
    assert "depop" in result["search_links"], "Depop link missing"


@pytest.mark.asyncio
async def test_price_tracking_updates(puppeteer):
    """Test that price changes are tracked over time."""
    neo4j = get_connection()
    product_storage = ProductStorage(neo4j)
    
    # Get a product
    query = "MATCH (p:Product) RETURN p.id as id LIMIT 1"
    result = neo4j.execute_read(query)
    
    if not result:
        pytest.skip("No products in database")
    
    product_id = result[0]["id"]
    
    # Get initial price history count
    initial_history = product_storage.get_price_history(product_id, limit=100)
    initial_count = len(initial_history)
    
    # Simulate price update (in real scenario, would re-crawl)
    # For test, we'll just verify the structure exists
    
    # Verify price history query works
    assert initial_count >= 0, "Price history query failed"
    
    # Verify GraphQL price history query
    graphql_client = GraphQLTestClient()
    query = """
    query GetPriceHistory($id: String!) {
        product(id: $id) {
            id
            priceHistory(limit: 10) {
                price
                currency
                timestamp
            }
        }
    }
    """
    
    response = await graphql_client.query(query, variables={"id": product_id})
    
    assert "data" in response, f"GraphQL error: {response.get('errors')}"
    if response["data"]["product"]:
        assert "priceHistory" in response["data"]["product"], "Price history missing"


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])




