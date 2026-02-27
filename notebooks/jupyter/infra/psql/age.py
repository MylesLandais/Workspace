"""Apache AGE adapter for Neo4j-compatible Cypher queries in PostgreSQL."""

import json
import logging
import re
from typing import Any, Dict, List, Optional, Tuple

from psycopg2.extras import RealDictCursor

from .connection import get_connection

logger = logging.getLogger(__name__)

# Regex to strip AGE type suffixes from agtype string values, e.g. ::vertex, ::edge
_AGTYPE_SUFFIX_RE = re.compile(r"::\w+$")


def _parse_agtype(val: Any) -> Any:
    """Strip AGE type suffixes and JSON-parse agtype string values."""
    if not isinstance(val, str):
        return val
    stripped = _AGTYPE_SUFFIX_RE.sub("", val.strip())
    try:
        return json.loads(stripped)
    except (ValueError, TypeError):
        return val


def _parse_return_columns(cypher: str) -> List[Tuple[str, str]]:
    """Extract column names from the last RETURN clause of a Cypher query.

    Returns a list of (name, "agtype") tuples. Falls back to [("result", "agtype")]
    when the RETURN clause cannot be parsed.
    """
    match = re.search(r"\bRETURN\b(.+?)(?:LIMIT|ORDER|SKIP|$)", cypher, re.IGNORECASE | re.DOTALL)
    if not match:
        return [("result", "agtype")]

    raw = match.group(1).strip()
    cols: List[Tuple[str, str]] = []
    for token in raw.split(","):
        token = token.strip()
        # Handle "expr AS alias" or bare identifiers like "c", "count(*)"
        alias_match = re.search(r"\bAS\s+(\w+)$", token, re.IGNORECASE)
        if alias_match:
            cols.append((alias_match.group(1), "agtype"))
        else:
            # Use the last word-like token as the column name
            name_match = re.search(r"(\w+)\s*$", token)
            if name_match:
                cols.append((name_match.group(1), "agtype"))
    return cols or [("result", "agtype")]


class AGEAdapter:
    """Provides a Neo4j-like interface using Apache AGE within PostgreSQL."""

    def __init__(self, graph_name: str = "archive_graph"):
        self.pg = get_connection()
        self.graph_name = graph_name
        self._initialized = False

    def _initialize_graph(self) -> None:
        """Ensure the AGE extension is loaded and the graph exists."""
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
                    except Exception as exc:
                        logger.debug("AGE setup query skipped: %s (%s)", q[:40], exc)
                conn.commit()
            self._initialized = True
        finally:
            conn.close()

    def execute_query(
        self,
        cypher: str,
        parameters: Optional[dict] = None,
        return_columns: Optional[List[Tuple[str, str]]] = None,
    ) -> List[Dict]:
        """Execute a Cypher query via AGE's cypher() function.

        Args:
            cypher: The Cypher query string.
            parameters: Optional dict of query parameters.
            return_columns: Explicit list of (col_name, col_type) pairs matching
                the Cypher RETURN clause. When None, the RETURN clause is parsed
                automatically.

        Returns:
            List of result dicts with agtype values deserialized to Python objects.
        """
        self._initialize_graph()

        if return_columns is None:
            return_columns = _parse_return_columns(cypher)

        cols_sql = ", ".join(f"{name} {typ}" for name, typ in return_columns)
        params_json = json.dumps(parameters or {})

        query = (
            f"SELECT * FROM cypher('{self.graph_name}', "
            f"$$ {cypher} $$, %s) AS ({cols_sql});"
        )

        conn = self.pg.get_raw_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute('SET search_path = ag_catalog, "$user", public;')
                cur.execute(query, (params_json,))
                rows = cur.fetchall()
                return [
                    {k: _parse_agtype(v) for k, v in dict(row).items()}
                    for row in rows
                ]
        finally:
            conn.close()

    def execute_write(
        self,
        cypher: str,
        parameters: Optional[dict] = None,
        return_columns: Optional[List[Tuple[str, str]]] = None,
    ) -> List[Dict]:
        """Execute a write Cypher query inside an explicit transaction."""
        self._initialize_graph()

        if return_columns is None:
            return_columns = _parse_return_columns(cypher)

        cols_sql = ", ".join(f"{name} {typ}" for name, typ in return_columns)
        params_json = json.dumps(parameters or {})

        query = (
            f"SELECT * FROM cypher('{self.graph_name}', "
            f"$$ {cypher} $$, %s) AS ({cols_sql});"
        )

        conn = self.pg.get_raw_connection()
        try:
            conn.autocommit = False
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute('SET search_path = ag_catalog, "$user", public;')
                cur.execute(query, (params_json,))
                rows = cur.fetchall()
                conn.commit()
                return [
                    {k: _parse_agtype(v) for k, v in dict(row).items()}
                    for row in rows
                ]
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.autocommit = True
            conn.close()

    def execute_read(
        self,
        cypher: str,
        parameters: Optional[dict] = None,
        return_columns: Optional[List[Tuple[str, str]]] = None,
    ) -> List[Dict]:
        """Execute a read-only Cypher query."""
        return self.execute_query(cypher, parameters, return_columns)

    def execute_cypher(self, cypher: str, params: Optional[dict] = None) -> List[Dict]:
        """Execute Cypher and return results as plain dicts (auto-parses agtype).

        This is the primary method for new code. Column names are auto-detected
        from the RETURN clause.
        """
        return self.execute_query(cypher, params)

    def close(self) -> None:
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
