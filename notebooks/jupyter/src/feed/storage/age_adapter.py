"""Apache AGE adapter for Neo4j-compatible graph queries in PostgreSQL."""

import os
from typing import Optional, Any, List, Dict
from .postgres_connection import get_postgres_connection

class AGEAdapter:
    """
    Adapter that provides a Neo4j-like interface but executes Cypher 
    using Apache AGE within a PostgreSQL database.
    """

    def __init__(self, graph_name: str = "archive_graph"):
        self.pg = get_postgres_connection()
        self.graph_name = graph_name
        self._initialized = False

    def _initialize_graph(self):
        """Ensure the graph and AGE extension are ready."""
        if not self._initialized:
            # AGE requires loading the extension and creating the graph
            setup_queries = [
                "CREATE EXTENSION IF NOT EXISTS age;",
                "LOAD 'age';",
                "SET search_path = ag_catalog, \"$user\", public;",
                f"SELECT create_graph('{self.graph_name}') WHERE NOT EXISTS (SELECT 1 FROM ag_catalog.ag_graph WHERE name = '{self.graph_name}');"
            ]
            conn = self.pg.get_raw_connection()
            try:
                with conn.cursor() as cur:
                    for q in setup_queries:
                        try:
                            cur.execute(q)
                        except Exception as e:
                            # create_graph might fail if it already exists, handled by WHERE NOT EXISTS if possible
                            # but sometimes it still throws.
                            pass
                    conn.commit()
                self._initialized = True
            finally:
                conn.close()

    def execute_query(self, cypher: str, parameters: Optional[dict] = None) -> List[Dict]:
        """Execute a Cypher query using Apache AGE's cypher() function."""
        self._initialize_graph()
        
        # Prepare parameters as JSON
        import json
        params_json = json.dumps(parameters or {})
        
        # We use a generic 'v agtype' return pattern for AGE.
        # This works best for MATCH (v) RETURN v queries.
        # For more complex multi-column returns, AGE needs explicit column definitions.
        
        # Determine if we are returning a single node or multiple columns
        # This is a heuristic for the migration.
        return_cols = "v agtype"
        if "RETURN count" in cypher:
            return_cols = "count agtype"
        
        query = f"SELECT * FROM cypher('{self.graph_name}', $$ {cypher} $$, %s) as ({return_cols});"
        
        conn = self.pg.get_raw_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Set search path for AGE
                cur.execute("SET search_path = ag_catalog, \"$user\", public;")
                cur.execute(query, (params_json,))
                results = cur.fetchall()
                # Process results from agtype to dict
                return [dict(r) for r in results]
        except Exception as e:
            print(f"AGE Query Error: {e}")
            return []
        finally:
            conn.close()

    def execute_write(self, query: str, parameters: Optional[dict] = None) -> List[Dict]:
        return self.execute_query(query, parameters)

    def execute_read(self, query: str, parameters: Optional[dict] = None) -> List[Dict]:
        return self.execute_query(query, parameters)

    def close(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

# Global instance for easy replacement of get_connection()
_age_adapter = None

def get_age_connection() -> AGEAdapter:
    global _age_adapter
    if _age_adapter is None:
        _age_adapter = AGEAdapter()
    return _age_adapter
