#!/usr/bin/env python3
"""Link Listal profile to Creator or create new Creator."""

from feed.storage.neo4j_connection import get_connection
from uuid import uuid4
from datetime import datetime

neo4j = get_connection()

# Create Creator for Maddie Teeuws
create_creator = """
MERGE (c:Creator {slug: $slug})
ON CREATE SET
    c.uuid = $uuid,
    c.name = $name,
    c.slug = $slug,
    c.created_at = datetime(),
    c.updated_at = datetime()
ON MATCH SET
    c.updated_at = datetime()
RETURN c
"""

result = neo4j.execute_write(create_creator, {
    "slug": "maddie-teeuws",
    "uuid": str(uuid4()),
    "name": "Maddie Teeuws"
})

print(f"Created Creator: {result[0]['c']['name']} ({result[0]['c']['slug']})")

# Link Creator to ListalProfile
link_rel = """
MATCH (c:Creator {slug: $slug})
MERGE (lp:ListalProfile {slug: $slug})
ON CREATE SET lp.name = $name, lp.url = $url, lp.discovered_at = datetime()
MERGE (c)-[:LISTAL_PROFILE]->(lp)
MERGE (lp)-[:SUBJECT_OF]->(c)
RETURN c.name, lp.slug
"""

result = neo4j.execute_write(link_rel, {
    "slug": "maddie-teeuws",
    "name": "Maddie Teeuws",
    "url": "https://www.listal.com/maddie-teeuws"
})

print(f"Linked: Creator->ListalProfile")

# Add HAS_IMAGE relationship
image_rel = """
MATCH (lp:ListalProfile {slug: $slug})
MATCH (li:ListalImage {subject_name: $name})
MERGE (lp)-[:HAS_IMAGE]->(li)
RETURN count(*) as count
"""

result = neo4j.execute_write(image_rel, {
    "slug": "maddie-teeuws",
    "name": "Maddie Teeuws"
})

print(f"Linked images: {result[0]['count']}")

# Full graph verification
print()
print("=== Full Graph ===")
result = neo4j.execute_read("""
MATCH (c:Creator {slug: "maddie-teeuws"})
MATCH (lp:ListalProfile)-[:SUBJECT_OF]->(c)
MATCH (lp)-[:HAS_IMAGE]->(li)
MATCH (li)-[:IN_LIST]->(ll:ListalList)
RETURN c.name as creator, lp.url as listal_url, count(li) as image_count, collect(ll.name)[..3] as sample_lists
""")
for r in result:
    print(f"Creator: {r['creator']}")
    print(f"  Listal: {r['listal_url']}")
    print(f"  Images: {r['image_count']}")
    print(f"  Sample lists: {r['sample_lists']}")
