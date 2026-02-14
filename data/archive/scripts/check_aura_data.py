#!/usr/bin/env python3
"""Check Neo4j Aura database for existing data."""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment
load_dotenv()

from neo4j import GraphDatabase

uri = os.getenv("NEO4J_URI")
username = os.getenv("NEO4J_USERNAME", "neo4j")
password = os.getenv("NEO4J_PASSWORD")

if not uri or not password:
    print("Error: NEO4J_URI or NEO4J_PASSWORD not set in .env")
    sys.exit(1)

driver = GraphDatabase.driver(uri, auth=(username, password))

print("=" * 80)
print("NEO4J AURA DATABASE CHECK")
print("=" * 80)
print(f"Connected to: {uri}")
print()

def run_query(query, description):
    """Run a query and return results."""
    with driver.session() as session:
        result = session.run(query)
        return [record for record in result]

# Get all labels
print("Node Labels and Counts:")
print("-" * 80)
labels_query = "CALL db.labels() YIELD label RETURN label ORDER BY label"
labels = run_query(labels_query, "labels")

for label_record in labels:
    label = label_record["label"]
    count_query = f"MATCH (n:{label}) RETURN count(n) as count"
    count_result = run_query(count_query, f"count_{label}")
    count = count_result[0]["count"] if count_result else 0
    print(f"  {label}: {count:,}")

print()
print("=" * 80)
print("IMAGE-RELATED DATA:")
print("-" * 80)

# Check WebPage nodes with images
webpage_query = """
MATCH (w:WebPage)
WHERE w.normalized_url CONTAINS '.jpg' 
   OR w.normalized_url CONTAINS '.png'
   OR w.normalized_url CONTAINS '.webp'
   OR w.normalized_url CONTAINS 'i.redd.it'
   OR w.normalized_url CONTAINS 'imgur'
RETURN count(w) as count
"""
result = run_query(webpage_query, "webpage_images")
webpage_count = result[0]["count"] if result else 0
print(f"WebPage nodes with image URLs: {webpage_count:,}")

# Check Post nodes with images
post_query = """
MATCH (p:Post)
WHERE p.url IS NOT NULL 
  AND (p.url CONTAINS '.jpg' OR p.url CONTAINS '.png' OR 
       p.url CONTAINS '.webp' OR p.url CONTAINS 'i.redd.it' OR
       p.url CONTAINS 'imgur')
RETURN count(p) as count
"""
result = run_query(post_query, "post_images")
post_count = result[0]["count"] if result else 0
print(f"Post nodes with image URLs: {post_count:,}")

# Check ImageFile nodes
imagefile_query = "MATCH (i:ImageFile) RETURN count(i) as count"
result = run_query(imagefile_query, "imagefiles")
imagefile_count = result[0]["count"] if result else 0
print(f"ImageFile nodes: {imagefile_count:,}")

# Check ImageCluster nodes
cluster_query = "MATCH (c:ImageCluster) RETURN count(c) as count"
result = run_query(cluster_query, "clusters")
cluster_count = result[0]["count"] if result else 0
print(f"ImageCluster nodes: {cluster_count:,}")

# Check repost relationships
repost_query = "MATCH ()-[r:REPOST_OF]->() RETURN count(r) as count"
result = run_query(repost_query, "reposts")
repost_count = result[0]["count"] if result else 0
print(f"REPOST_OF relationships: {repost_count:,}")

if imagefile_count > 0 or cluster_count > 0:
    print()
    print("=" * 80)
    print("DUPLICATE DETECTION RESULTS:")
    print("-" * 80)
    
    # Top reposted
    top_query = """
    MATCH (c:ImageCluster)
    WHERE c.repost_count > 0
    OPTIONAL MATCH (c)-[:CANONICAL]->(canonical:ImageFile)
    RETURN c.id as cluster_id,
           c.repost_count as reposts,
           c.canonical_sha256 as sha256
    ORDER BY c.repost_count DESC
    LIMIT 10
    """
    top_result = run_query(top_query, "top_reposts")
    
    if top_result:
        print("Top 10 Most Reposted Images:")
        print("Rank".ljust(6) + "Reposts".ljust(10) + "Cluster ID")
        print("-" * 80)
        for i, record in enumerate(top_result, 1):
            cluster_id = (record.get("cluster_id") or "")[:60]
            reposts = record.get("reposts") or 0
            print(str(i).ljust(6) + str(reposts).ljust(10) + cluster_id)

print()
print("=" * 80)

driver.close()







