"""Nix environment management service.

Handles pre-built environment registration, cache management, and cleanup.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone as tz

logger = logging.getLogger(__name__)


class NixEnvironmentService:
    """Manage pre-built nix-shell environments."""

    def __init__(self, postgres_connection, nix_runner=None):
        """Initialize with PostgreSQL connection and optional NixRunner.

        Args:
            postgres_connection: PostgresConnection instance
            nix_runner: Optional NixRunner instance for building environments
        """
        self.pg = postgres_connection
        self.nix_runner = nix_runner

    def register_environment(
        self,
        hash_val: str,
        packages: List[str],
        drv_path: str,
        store_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Register a pre-built nix environment in the database.

        Args:
            hash_val: SHA256 hash of package specification
            packages: List of nix packages
            drv_path: Path to .drv file
            store_path: Optional path to built store derivation

        Returns:
            Dict with environment metadata

        Raises:
            RuntimeError: If database operation fails
        """
        try:
            import json

            self.pg.execute_write(
                """
                INSERT INTO nix_environments (
                    hash, packages, drv_path, store_path, use_count, last_used_at, created_at
                ) VALUES (
                    %s, %s, %s, %s, 1, %s, %s
                )
                ON CONFLICT (hash) DO UPDATE
                SET use_count = nix_environments.use_count + 1, last_used_at = %s
                """,
                (
                    hash_val,
                    json.dumps(packages),
                    drv_path,
                    store_path,
                    datetime.now(tz.utc),
                    datetime.now(tz.utc),
                    datetime.now(tz.utc),
                )
            )

            logger.info(f"Registered nix environment {hash_val[:8]} with {len(packages)} packages")

            return {
                "hash": hash_val,
                "packages": packages,
                "drv_path": drv_path,
                "store_path": store_path,
                "use_count": 1,
            }

        except Exception as e:
            logger.error(f"Failed to register environment: {e}")
            raise RuntimeError(f"Database error: {e}")

    def get_environment(self, hash_val: str) -> Optional[Dict[str, Any]]:
        """Get cached environment by hash.

        Args:
            hash_val: SHA256 hash of package specification

        Returns:
            Dict with environment metadata or None if not found
        """
        try:
            result = self.pg.execute_read(
                """
                SELECT hash, packages, drv_path, store_path, use_count, last_used_at
                FROM nix_environments
                WHERE hash = %s
                """,
                (hash_val,)
            )

            if result:
                row = result[0]
                import json
                return {
                    "hash": row[0],
                    "packages": json.loads(row[1]) if isinstance(row[1], str) else row[1],
                    "drv_path": row[2],
                    "store_path": row[3],
                    "use_count": row[4],
                    "last_used_at": row[5],
                }
            return None

        except Exception as e:
            logger.error(f"Failed to get environment {hash_val}: {e}")
            return None

    def list_environments(
        self,
        limit: int = 100,
        offset: int = 0,
        order_by: str = "last_used_at",
    ) -> List[Dict[str, Any]]:
        """List all cached nix environments.

        Args:
            limit: Maximum results (default 100)
            offset: Pagination offset (default 0)
            order_by: Order field (default "last_used_at")

        Returns:
            List of environment dicts
        """
        allowed_fields = {"last_used_at", "use_count", "created_at", "hash"}
        if order_by not in allowed_fields:
            order_by = "last_used_at"

        try:
            query = f"""
                SELECT hash, packages, drv_path, store_path, use_count, last_used_at, created_at
                FROM nix_environments
                ORDER BY {order_by} DESC
                LIMIT %s OFFSET %s
            """

            results = self.pg.execute_read(query, (limit, offset))
            envs = []

            for row in results:
                import json
                envs.append({
                    "hash": row[0],
                    "packages": json.loads(row[1]) if isinstance(row[1], str) else row[1],
                    "drv_path": row[2],
                    "store_path": row[3],
                    "use_count": row[4],
                    "last_used_at": row[5],
                    "created_at": row[6],
                })

            logger.debug(f"Retrieved {len(envs)} environments")
            return envs

        except Exception as e:
            logger.error(f"Failed to list environments: {e}")
            return []

    def get_environment_stats(self) -> Dict[str, Any]:
        """Get statistics about cached environments.

        Returns:
            Dict with stats:
            {
                "total_environments": int,
                "total_uses": int,
                "average_uses": float,
                "most_used_hash": str,
                "total_packages": int,
            }
        """
        try:
            stats = self.pg.execute_read(
                """
                SELECT
                    COUNT(*) as total,
                    SUM(use_count) as total_uses,
                    AVG(use_count) as avg_uses,
                    (SELECT hash FROM nix_environments ORDER BY use_count DESC LIMIT 1) as most_used
                FROM nix_environments
                """
            )

            if stats:
                row = stats[0]
                return {
                    "total_environments": row[0] or 0,
                    "total_uses": row[1] or 0,
                    "average_uses": row[2] or 0,
                    "most_used_hash": row[3],
                }
            return {}

        except Exception as e:
            logger.error(f"Failed to get environment stats: {e}")
            return {}

    def cleanup_stale_environments(self, days: int = 30) -> int:
        """Delete nix environments unused for N days.

        Args:
            days: Number of days of inactivity (default 30)

        Returns:
            Number of environments deleted
        """
        try:
            result = self.pg.execute_write(
                """
                DELETE FROM nix_environments
                WHERE last_used_at < NOW() - INTERVAL '%s days'
                """,
                (days,)
            )

            deleted_count = result if isinstance(result, int) else 0
            logger.info(f"Cleaned up {deleted_count} nix environments (unused for {days} days)")
            return deleted_count

        except Exception as e:
            logger.error(f"Failed to cleanup environments: {e}")
            return 0

    def build_and_register(
        self,
        packages: List[str],
        force_rebuild: bool = False,
    ) -> Optional[str]:
        """Build and register a nix environment (requires NixRunner).

        Args:
            packages: List of nix packages
            force_rebuild: Rebuild even if cached (default False)

        Returns:
            .drv path if successful, None otherwise

        Raises:
            RuntimeError: If NixRunner not available or build fails
        """
        if not self.nix_runner:
            raise RuntimeError("NixRunner not available for environment building")

        from src.feed.scheduler.nix_runner import NixRunner

        hash_val = NixRunner.hash_package_spec(packages)

        # Check cache unless force rebuild
        if not force_rebuild:
            cached = self.get_environment(hash_val)
            if cached:
                logger.info(f"Using cached environment {hash_val[:8]}")
                return cached["drv_path"]

        # Build new environment
        logger.info(f"Building new nix environment for {len(packages)} packages")
        drv_path, was_cached = self.nix_runner.get_or_build_shell(packages)

        # Register in database
        self.register_environment(
            hash_val=hash_val,
            packages=packages,
            drv_path=drv_path,
        )

        return drv_path

    def get_most_used_environments(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most frequently used environments.

        Args:
            limit: Number of results (default 10)

        Returns:
            List of environment dicts ordered by use_count
        """
        try:
            results = self.pg.execute_read(
                """
                SELECT hash, packages, use_count, last_used_at
                FROM nix_environments
                ORDER BY use_count DESC
                LIMIT %s
                """,
                (limit,)
            )

            envs = []
            for row in results:
                import json
                envs.append({
                    "hash": row[0],
                    "packages": json.loads(row[1]) if isinstance(row[1], str) else row[1],
                    "use_count": row[2],
                    "last_used_at": row[3],
                })

            return envs

        except Exception as e:
            logger.error(f"Failed to get most used environments: {e}")
            return []
