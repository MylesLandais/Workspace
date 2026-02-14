"""PostgreSQL extension management: AGE and pgVector init, health checks."""

import logging
from typing import Dict, Any

from .connection import get_connection

logger = logging.getLogger(__name__)

REQUIRED_EXTENSIONS = ["age", "vector"]


def ensure_extensions() -> None:
    """Create required PostgreSQL extensions if they don't exist."""
    conn = get_connection().get_raw_connection()
    try:
        with conn.cursor() as cur:
            for ext in REQUIRED_EXTENSIONS:
                cur.execute(f"CREATE EXTENSION IF NOT EXISTS {ext};")
                logger.info("Ensured extension: %s", ext)
        conn.commit()
    finally:
        conn.close()


def health_check() -> Dict[str, Any]:
    """Check database connectivity and list installed extensions."""
    try:
        conn = get_connection().get_raw_connection()
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

    try:
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
            cur.fetchone()

            cur.execute("SELECT extname FROM pg_extension")
            rows = cur.fetchall()
            extensions = [r[0] for r in rows]

        return {"status": "healthy", "extensions": extensions}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}
    finally:
        conn.close()
