#!/usr/bin/env python3
from feed.storage.neo4j_connection import get_connection
n = get_connection()

# Get detailed data for the two fully crawled images
r = n.execute_read("""
MATCH (li:ListalImage {image_id: "16806755"})
RETURN li.views, li.subject_name, li.image_path, li.sha256, li.cached_at
""")
print("=== Image 16806755 ===")
for rec in r:
    print(f"  Subject: {rec['li.subject_name']}")
    print(f"  Views: {rec['li.views']}")
    print(f"  Cache: {rec['li.image_path']}")
    print(f"  SHA256: {rec['li.sha256']}")
    print(f"  Cached: {rec['li.cached_at']}")

# Get curated lists for 16806755
r = n.execute_read("""
MATCH (li:ListalImage {image_id: "16806755"})-[:IN_LIST]->(l:ListalList)
RETURN l.name, l.url
""")
print("\n=== Curated Lists (16806755) ===")
for rec in r:
    print(f"  {rec['l.name']}")
    print(f"    {rec['l.url']}")

# Get voters for 26229169
r = n.execute_read("""
MATCH (li:ListalImage {image_id: "26229169"})<-[:VOTED_FOR]-(u:ListalUser)
RETURN u.username
""")
print("\n=== Voters (26229169) ===")
for rec in r:
    print(f"  {rec['u.username']}")

# Get similar images
r = n.execute_read("""
MATCH (li:ListalImage {image_id: "16806755"})-[:SIMILAR_TO]->(sim)
RETURN sim.image_id
""")
print("\n=== Similar Images (16806755) ===")
similar = [rec['sim.image_id'] for rec in r]
print(f"  {similar}")
