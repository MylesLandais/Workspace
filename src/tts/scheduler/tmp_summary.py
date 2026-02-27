#!/usr/bin/env python3
from feed.storage.neo4j_connection import get_connection
n = get_connection()

# Full summary
r = n.execute_read("MATCH (li:ListalImage) WHERE li.views IS NOT NULL RETURN count(li) as total, sum(li.views) as total_views")
print(f"=== Graph Summary ===")
print(f"Images with full data: {r[0]['total']}")
print(f"Total views: {r[0]['total_views']}")

r = n.execute_read("MATCH (l:ListalList) RETURN count(l) as count")
print(f"Curated lists: {r[0]['count']}")

r = n.execute_read("MATCH ()-[r:IN_LIST]->() RETURN count(r) as count")
print(f"Image->List links: {r[0]['count']}")

r = n.execute_read("MATCH ()-[r:SIMILAR_TO]->() RETURN count(r) as count")
print(f"Similar image links: {r[0]['count']}")

print("\n=== Top Images by Views ===")
r = n.execute_read("MATCH (li:ListalImage) WHERE li.views IS NOT NULL RETURN li.image_id, li.subject_name, li.views ORDER BY li.views DESC LIMIT 10")
for rec in r:
    print(f"  {rec['li.image_id']}: {rec['li.subject_name']} ({rec['li.views']} views)")

print("\n=== Top Lists by Image Count ===")
r = n.execute_read("MATCH (l:ListalList)<-[:IN_LIST]-(i:ListalImage) WITH l, count(i) as cnt RETURN l.name, cnt ORDER BY cnt DESC LIMIT 10")
for rec in r:
    print(f"  {rec['l.name']}: {rec['cnt']} images")

print("\n=== Subjects (People) ===")
r = n.execute_read("""
MATCH (li:ListalImage) WHERE li.views IS NOT NULL
WITH li.subject_name as name, count(li) as img_count, sum(li.views) as total_views
RETURN name, img_count, total_views
ORDER BY total_views DESC
LIMIT 10
""")
for rec in r:
    print(f"  {rec['name']}: {rec['img_count']} images, {rec['total_views']} views")

print("\n=== Cross-Reference Network ===")
r = n.execute_read("""
MATCH (l:ListalList)<-[:IN_LIST]-(i1:ListalImage)
WITH l, collect(i1) as images
WHERE size(images) > 1
UNWIND images as i1
UNWIND images as i2
WITH l, i1, i2 WHERE id(i1) < id(i2)
RETURN l.name as list_name, count(*) as pairs
ORDER BY pairs DESC
LIMIT 5
""")
for rec in r:
    print(f"  {rec['list_name']}: {rec['pairs']} co-occurrences")
