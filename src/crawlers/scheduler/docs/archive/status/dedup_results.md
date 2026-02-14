# Duplicate Detection Results

## Current Status

**Date:** 2025-01-15

### Summary
No duplicate detection has been run yet. The database shows:

- **Total Images Processed:** 0
- **Total Clusters:** 0  
- **Total Repost Relationships:** 0
- **Posts in Database:** 0

## Next Steps

To populate the duplicate detection results, you need to:

1. **Ensure Posts exist in Neo4j** - Run the feed ingestion pipeline first
2. **Apply the Schema** - Run the Neo4j schema migration:
   ```cypher
   :source src/image_dedup/schema/neo4j_schema.cypher
   ```
3. **Run Batch Processing** - Process existing posts through deduplication:
   ```bash
   python -m src.image_dedup.batch_process
   ```

## Expected Output Format

Once batch processing is complete, the results will show:

```
================================================================================
DUPLICATE DETECTION RESULTS
================================================================================

Total Images Processed: X,XXX
Total Clusters: X,XXX
Total Repost Relationships: X,XXX
Clusters with Reposts: XXX
Repost Rate: XX.XX%

--------------------------------------------------------------------------------
TOP 10 MOST REPOSTED IMAGES:
--------------------------------------------------------------------------------
Rank   Reposts    Cluster ID                            Subreddit          
--------------------------------------------------------------------------------
1       42        550e8400-e29b-41d4-a716-446655440000  memes              
2       38        6ba7b810-9dad-11d1-80b4-00c04fd430c8  dankmemes          
...

--------------------------------------------------------------------------------
DUPLICATE DETECTION METHODS:
--------------------------------------------------------------------------------
Method               Count      
------------------------------
phash                1250       
sha256               890        
phash+dhash          320        
clip                 45         
```

## To Get Results

Run this query in Neo4j Browser or use the Python script:

```python
from src.image_dedup.query_results import main
main()
```

Or use the detailed analysis:

```python
from src.image_dedup.analyze_results import main
main()
```






