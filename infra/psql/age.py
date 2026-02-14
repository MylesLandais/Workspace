"""Apache AGE adapter for Neo4j-compatible Cypher queries in PostgreSQL."""

import json
import logging
from typing import Optional, List, Dict

from psycopg2.extras import RealDictCursor

from .connection import get_connection

logger = logging.getLogger(__name__)


class AGEAdapter:
    """Provides a Neo4j-like interface using Apache AGE within PostgreSQL."""

    def __init__(self, graph_name: str = "archive_graph"):
        self.pg = get_connection()
        self.graph_name = graph_name
        self._initialized = False

    def _initialize_graph(self):
        """Ensure the AGE extension is loaded and graph exists."""
        if self._initialized:
            return

        setup_queries = [
            "CREATE EXTENSION IF NOT EXISTS age;",
            "LOAD 'age';",
            'SET search_path = ag_catalog, "$user", public;',
            (
                f"SELECT create_graph('{self.graph_name}') "
                f"WHERE NOT EXISTS ("
                f"SELECT 1 FROM ag_catalog.ag_graph "
                f"WHERE name = '{self.graph_name}'"
                f");"
            ),
        ]

        conn = self.pg.get_raw_connection()
        try:
            with conn.cursor() as cur:
                for q in setup_queries:
                    try:
                        cur.execute(q)
                    except Exception as e:
                        logger.debug("AGE setup query skipped: %s (%s)", q[:40], e)
                conn.commit()
            self._initialized = True
        finally:
            conn.close()

    def execute_query(
        self, cypher: str, parameters: Optional[dict] = None
    ) -> List[Dict]:
        """Execute a Cypher query via AGE's cypher() function."""
        self._initialize_graph()

        params_json = json.dumps(parameters or {})

        return_cols = "v agtype"
        if "RETURN count" in cypher:
            return_cols = "count agtype"

        query = (
            f"SELECT * FROM cypher('{self.graph_name}', "
            f"$$ {cypher} $$, %s) as ({return_cols});"
        )

        conn = self.pg.get_raw_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute('SET search_path = ag_catalog, "$user", public;')
                cur.execute(query, (params_json,))
                results = cur.fetchall()
                return [dict(r) for r in results]
        finally:
            conn.close()

    def execute_write(
        self, query: str, parameters: Optional[dict] = None
    ) -> List[Dict]:
        """Execute a write Cypher query."""
        return self.execute_query(query, parameters)

    def execute_read(
        self, query: str, parameters: Optional[dict] = None
    ) -> List[Dict]:
        """Execute a read-only Cypher query."""
        return self.execute_query(query, parameters)

    def close(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


_age_adapter: Optional[AGEAdapter] = None


def get_age(graph_name: str = "archive_graph") -> AGEAdapter:
    """Get the singleton AGEAdapter instance."""
    global _age_adapter
    if _age_adapter is None:
        _age_adapter = AGEAdapter(graph_name=graph_name)
    return _age_adapter
