"""Product REST endpoints (replaces ecommerce_schema.py GraphQL)."""

from fastapi import APIRouter, Query, HTTPException
from typing import Optional

from lib.db.client import get_db

router = APIRouter(prefix="/api/products", tags=["products"])


@router.get("/")
async def list_products(
    brand: Optional[str] = None,
    category: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """List products with optional filtering."""
    db = get_db()
    query = "SELECT * FROM products"
    params = {}
    conditions = []

    if brand:
        conditions.append("brand = %(brand)s")
        params["brand"] = brand
    if category:
        conditions.append("category = %(category)s")
        params["category"] = category

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " ORDER BY updated_at DESC LIMIT %(limit)s OFFSET %(offset)s"
    params["limit"] = limit
    params["offset"] = offset

    return db.execute_query(query, params)


@router.get("/{product_id}")
async def get_product(product_id: int):
    """Get a single product by ID."""
    db = get_db()
    results = db.execute_query(
        "SELECT * FROM products WHERE id = %(id)s", {"id": product_id}
    )
    if not results:
        raise HTTPException(status_code=404, detail="Product not found")
    return results[0]
