from neo4j import GraphDatabase
import psycopg2
import json
import os

# Neo4j Config
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://n4j.jupyter.dev.local:7687")
NEO4J_USER = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PW = os.getenv("NEO4J_PASSWORD", "password")

# Postgres Config
PG_CONN = "host=archive_postgres dbname=archive_system user=postgres password=secret"

def serialize_props(props):
    """Convert Neo4j types to JSON serializable types."""
    clean = {}
    for k, v in props.items():
        if hasattr(v, 'isoformat'):
            clean[k] = v.isoformat()
        elif hasattr(v, 'to_native'): # Neo4j types sometimes have this
            clean[k] = str(v.to_native())
        else:
            clean[k] = v
    return clean

def migrate_graph():
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PW))
    pg_conn = psycopg2.connect(PG_CONN)
    
    labels_to_migrate = ['Subreddit', 'Creator', 'Entity', 'Platform']
    
    try:
        with driver.session() as session:
            for label in labels_to_migrate:
                print(f"Migrating {label} nodes...")
                result = session.run(f"MATCH (n:{label}) RETURN n")
                nodes = [dict(record['n']) for record in result]
                
                if not nodes:
                    print(f"No {label} nodes found.")
                    continue
                
                with pg_conn.cursor() as cur:
                    cur.execute("SET search_path = ag_catalog, \"$user\", public;")
                    for props in nodes:
                        # Clean up properties for JSON
                        # Escape quotes in keys and values manually if needed, but json.dumps handles values.
                        # The issue is likely how we embed this into the cypher string.
                        # We need to ensure the JSON string is properly escaped for SQL.
                        
                        # Use parameterized query instead of f-string injection
                        props_json = json.dumps(serialize_props(props))
                        
                        # Apache AGE requires a very specific syntax for creating nodes with properties.
                        # We cannot easily pass JSON as a parameter to CREATE via the cypher() function call in the same way as Neo4j.
                        # We have to construct the map string manually for Cypher: {key: "value", ...}
                        
                        # Construct Cypher map string manually
                        props_map_parts = []
                        for k, v in serialize_props(props).items():
                            # Escape double quotes in values
                            if isinstance(v, str):
                                v_escaped = v.replace('"', '\\"').replace('\n', '\\n')
                                props_map_parts.append(f'{k}: "{v_escaped}"')
                            elif isinstance(v, bool):
                                props_map_parts.append(f'{k}: {str(v).lower()}')
                            elif v is None:
                                pass # Skip None values
                            else:
                                props_map_parts.append(f'{k}: {v}')
                        
                        props_str = "{" + ", ".join(props_map_parts) + "}"
                        
                        cypher = f"CREATE (:{label} {props_str})"
                        
                        # Execute using the cypher function
                        # Note: We need to escape single quotes in the cypher string itself for the SQL string
                        cypher_sql = cypher.replace("'", "''")
                        query = f"SELECT * FROM cypher('archive_graph', $$ {cypher} $$) as (v agtype);"
                        try:
                            cur.execute(query)
                        except Exception as e:
                            print(f"Failed to create node: {e}")
                    pg_conn.commit()
                print(f"Migrated {len(nodes)} {label} nodes.")
                
    finally:
        driver.close()
        pg_conn.close()

if __name__ == "__main__":
    migrate_graph()
