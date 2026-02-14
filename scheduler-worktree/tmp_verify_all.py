#!/usr/bin/env python3
from feed.storage.neo4j_connection import get_connection
neo4j = get_connection()
r = neo4j.execute_read("MATCH (li:ListalImage) RETURN li.image_id, li.views, li.sha256, li.subject_name ORDER BY li.image_id")
print("=== Listal Images in Neo4j ===")
for rec in r:
    sha = rec["li.sha256"][:16]
    print(f"  {rec['li.image_id']}: {rec['li.subject_name']} ({rec['li.views']} views, {sha}...)")
