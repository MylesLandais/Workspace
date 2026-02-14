"""Integration tests for GraphQL schema validation."""

import pytest
from feed.graphql.schema import schema
import strawberry


def test_schema_creation():
    """Test that GraphQL schema is created successfully."""
    assert schema is not None
    assert isinstance(schema, strawberry.Schema)


def test_schema_introspection():
    """Test GraphQL schema introspection."""
    # Get schema types
    query_type = schema.query_type
    assert query_type is not None
    
    # Check for e-commerce fields
    fields = {field.name for field in query_type.fields}
    
    # E-commerce fields
    assert "product" in fields, "product field missing"
    assert "products" in fields, "products field missing"
    assert "searchProducts" in fields, "searchProducts field missing"
    assert "garmentStyle" in fields, "garmentStyle field missing"
    assert "garmentStyles" in fields, "garmentStyles field missing"
    assert "similarStyles" in fields, "similarStyles field missing"
    
    # Reddit fields
    assert "posts" in fields, "posts field missing"
    assert "stats" in fields, "stats field missing"
    
    # Creator fields
    assert "creator" in fields, "creator field missing"
    assert "creators" in fields, "creators field missing"


def test_product_type_fields():
    """Test Product type has all required fields."""
    product_type = schema.get_type_by_name("Product")
    assert product_type is not None
    
    fields = {field.name for field in product_type.fields}
    
    required_fields = {
        "id", "title", "description", "price", "currency", "status",
        "brand", "condition", "size", "category", "tags", "imageUrls",
        "sellerUsername", "likesCount", "createdUtc", "url",
        "images", "seller", "priceHistory"
    }
    
    for field in required_fields:
        assert field in fields, f"Product field '{field}' missing"


def test_garment_style_type_fields():
    """Test GarmentStyle type has all required fields."""
    style_type = schema.get_type_by_name("GarmentStyle")
    assert style_type is not None
    
    fields = {field.name for field in style_type.fields}
    
    required_fields = {
        "uuid", "name", "category", "garmentType", "primaryStyle",
        "description", "color", "fit", "length", "material",
        "features", "matchedProducts"
    }
    
    for field in required_fields:
        assert field in fields, f"GarmentStyle field '{field}' missing"


def test_schema_export():
    """Test that schema can be exported as SDL."""
    sdl = schema.as_str()
    assert "type Product" in sdl
    assert "type GarmentStyle" in sdl
    assert "type Query" in sdl
    assert "query product" in sdl.lower() or "product(" in sdl




