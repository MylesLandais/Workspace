#!/usr/bin/env python3
"""Verify Neo4j data for Listal image 26229169."""

from feed.storage.neo4j_connection import get_connection

neo4j = get_connection()

print('=== ListalImage ===')
result = neo4j.execute_read('MATCH (li:ListalImage {image_id: "26229169"}) RETURN li')
for r in result:
    print(dict(r['li']))

print()
print('=== Related Images (first 5) ===')
result = neo4j.execute_read('MATCH (li:ListalImage {image_id: "26229169"})-[:SIMILAR_TO]->(r) RETURN r.image_id, r.subject_name LIMIT 5')
for r in result:
    print(f"  {r['r.image_id']}: {r['r.subject_name']}")

print()
print('=== Curated Lists ===')
result = neo4j.execute_read('MATCH (li:ListalImage {image_id: "26229169"})-[:IN_LIST]->(l:ListalList) RETURN l.name, l.url')
for r in result:
    print(f"  {r['l.name']}: {r['l.url']}")

print()
print('=== ListalProfile ===')
result = neo4j.execute_read('MATCH (lp:ListalProfile {slug: "maddie-teeuws"}) RETURN lp')
for r in result:
    print(dict(r['lp']))
