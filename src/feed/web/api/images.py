"""Image search REST endpoints (replaces image_search_schema.py GraphQL)."""

from fastapi import APIRouter, Query, HTTPException
from typing import Optional

from lib.db.client import get_db

router = APIRouter(prefix="/api/images", tags=["images"])


@router.get("/search")
async def search_images(
    q: Optional[str] = None,
    creator: Optional[str] = None,
    platform: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """Search images by tags, creator, or platform."""
    db = get_db()
    query = "SELECT * FROM images"
    params = {}
    conditions = []

    if q:
        conditions.append("tags ILIKE %(q)s")
        params["q"] = f"%{q}%"
    if creator:
        conditions.append("creator_name = %(creator)s")
        params["creator"] = creator
    if platform:
        conditions.append("platform = %(platform)s")
        params["platform"] = platform

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " ORDER BY created_at DESC LIMIT %(limit)s OFFSET %(offset)s"
    params["limit"] = limit
    params["offset"] = offset

    return db.execute_query(query, params)
