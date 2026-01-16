# Quick Queries for Duplicate Detection Results

Run these queries directly in Neo4j Browser or via Cypher to see duplicate detection results.

## Overall Statistics

```cypher
// Total images processed
MATCH (i:ImageFile)
RETURN count(i) as total_images;

// Total clusters
MATCH (c:ImageCluster)
RETURN count(c) as total_clusters;

// Total repost relationships
MATCH ()-[r:REPOST_OF]->()
RETURN count(r) as total_reposts;

// Clusters with reposts
MATCH (c:ImageCluster)
WHERE c.repost_count > 0
RETURN count(c) as clusters_with_reposts;
```

## Top Reposted Images

```cypher
MATCH (c:ImageCluster)
WHERE c.repost_count > 0
OPTIONAL MATCH (c)-[:CANONICAL]->(canonical:ImageFile)
OPTIONAL MATCH (canonical)-[:APPEARED_IN]->(p:Post)
RETURN c.id as cluster_id,
       c.repost_count as reposts,
       c.first_seen as first_seen,
       c.last_seen as last_seen,
       c.canonical_sha256 as sha256,
       collect(DISTINCT p.subreddit)[0] as subreddit,
       collect(DISTINCT p.title)[0] as title
ORDER BY c.repost_count DESC
LIMIT 20;
```

## Duplicate Detection Methods

```cypher
MATCH ()-[r:REPOST_OF]->()
WITH r.detected_method as method, count(*) as count
RETURN method, count
ORDER BY count DESC;
```

## Cluster Size Distribution

```cypher
MATCH (c:ImageCluster)<-[:BELONGS_TO]-(i:ImageFile)
WITH c, count(i) as size
WITH size, count(c) as count
RETURN size, count
ORDER BY size ASC;
```

## Find Duplicates for a Specific Image

```cypher
// Replace 'image-uuid' with actual image ID
MATCH (i:ImageFile {id: 'image-uuid'})-[:BELONGS_TO]->(c:ImageCluster)
MATCH (c)<-[:BELONGS_TO]-(other:ImageFile)
RETURN i, other, c
ORDER BY other.created_at ASC;
```

## Repost Chain (Lineage)

```cypher
// Replace 'image-uuid' with actual image ID
MATCH path = (original:ImageFile)<-[:REPOST_OF*]-(repost:ImageFile)
WHERE original.id = 'image-uuid' OR repost.id = 'image-uuid'
RETURN path
ORDER BY length(path) DESC
LIMIT 1;
```

## Images by Subreddit

```cypher
MATCH (p:Post {subreddit: 'memes'})<-[:APPEARED_IN]-(i:ImageFile)-[:BELONGS_TO]->(c:ImageCluster)
RETURN count(DISTINCT i) as images,
       count(DISTINCT c) as clusters,
       sum(c.repost_count) as total_reposts,
       avg(c.repost_count) as avg_reposts_per_cluster;
```

## Recent Duplicate Detections

```cypher
MATCH (new:ImageFile)-[r:REPOST_OF]->(original:ImageFile)
WHERE r.detected_at >= datetime() - duration({days: 7})
RETURN new.id as new_image,
       original.id as original_image,
       r.detected_method as method,
       r.confidence as confidence,
       r.detected_at as detected_at
ORDER BY r.detected_at DESC
LIMIT 50;
```

## Python Script Usage

You can also run the Python script:

```bash
# In Docker container
docker exec -it <container> python /home/jovyan/workspaces/src/image_dedup/query_results.py

# Or using the analyze_results script for detailed analysis
docker exec -it <container> python /home/jovyan/workspaces/src/image_dedup/analyze_results.py
```







