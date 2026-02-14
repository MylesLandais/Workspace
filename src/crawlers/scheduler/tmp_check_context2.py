#!/usr/bin/env python3
from feed.storage.neo4j_connection import get_connection
n = get_connection()

# Check relationships for 16806755
print("=== Relationships for 16806755 ===")
r = n.execute_read("MATCH (li:ListalImage {image_id: '16806755'}) OPTIONAL MATCH (li)-[:IN_LIST]->(l) OPTIONAL MATCH (li)-[:SIMILAR_TO]->(sim) RETURN li.image_id, count(l) as lc, count(sim) as sc")
for rec in r:
    print(f"  Lists: {rec['lc']}, Similar: {rec['sc']}")

# Check what lists exist
print("\n=== All Listal Lists ===")
r = n.execute_read("MATCH (l:ListalList) RETURN l.name, l.slug LIMIT 10")
for rec in r:
    print(f"  {rec['l.name']}: {rec['l.slug']}")

# Check what users exist
print("\n=== All Listal Users ===")
r = n.execute_read("MATCH (u:ListalUser) RETURN u.username LIMIT 10")
for rec in r:
    print(f"  {rec['u.username']}")

# Check lists linked to 26229169
print("\n=== Lists for 26229169 ===")
r = n.execute_read("MATCH (li:ListalImage {image_id: '26229169'})-[:IN_LIST]->(l) RETURN l.name")
for rec in r:
    print(f"  {rec['l.name']}")

# Check similar images for 26229169
print("\n=== Similar images for 26229169 ===")
r = n.execute_read("MATCH (li:ListalImage {image_id: '26229169'})-[:SIMILAR_TO]->(sim) RETURN sim.image_id")
for rec in r:
    print(f"  {rec['sim.image_id']}")
