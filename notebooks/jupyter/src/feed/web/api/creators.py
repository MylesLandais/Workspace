"""Creator REST endpoints (replaces creator_schema.py GraphQL)."""

from fastapi import APIRouter, Query, HTTPException
from typing import Optional, List

from lib.db.client import get_db

router = APIRouter(prefix="/api/creators", tags=["creators"])


@router.get("/")
async def list_creators(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    platform: Optional[str] = None,
):
    """List creators with optional platform filter."""
    db = get_db()
    query = "SELECT * FROM creators"
    params = {}
    conditions = []

    if platform:
        conditions.append("platform = %(platform)s")
        params["platform"] = platform

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " ORDER BY updated_at DESC LIMIT %(limit)s OFFSET %(offset)s"
    params["limit"] = limit
    params["offset"] = offset

    return db.execute_query(query, params)


@router.get("/{creator_id}")
async def get_creator(creator_id: int):
    """Get a single creator by ID."""
    db = get_db()
    results = db.execute_query(
        "SELECT * FROM creators WHERE id = %(id)s", {"id": creator_id}
    )
    if not results:
        raise HTTPException(status_code=404, detail="Creator not found")
    return results[0]


@router.post("/")
async def create_creator(name: str, platform: str, handle: str):
    """Create a new creator record."""
    db = get_db()
    db.execute_query(
        "INSERT INTO creators (name, platform, handle) VALUES (%(name)s, %(platform)s, %(handle)s)",
        {"name": name, "platform": platform, "handle": handle},
    )
    return {"status": "created", "name": name}
