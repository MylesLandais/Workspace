#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from feed.storage.neo4j_connection import get_connection

neo4j = get_connection()

print('=' * 80)
print('DUPLICATE DETECTION RESULTS')
print('=' * 80)

# Count total images
query = 'MATCH (i:ImageFile) RETURN count(i) as count'
result = neo4j.execute_read(query)
total_images = result[0]['count'] if result else 0
print(f'\nTotal Images Processed: {total_images:,}')

# Count clusters
query = 'MATCH (c:ImageCluster) RETURN count(c) as count'
result = neo4j.execute_read(query)
total_clusters = result[0]['count'] if result else 0
print(f'Total Clusters: {total_clusters:,}')

# Count reposts
query = 'MATCH ()-[r:REPOST_OF]->() RETURN count(r) as count'
result = neo4j.execute_read(query)
total_reposts = result[0]['count'] if result else 0
print(f'Total Repost Relationships: {total_reposts:,}')

# Clusters with reposts
query = '''
MATCH (c:ImageCluster)
WHERE c.repost_count > 0
RETURN count(c) as count
'''
result = neo4j.execute_read(query)
clusters_with_reposts = result[0]['count'] if result else 0
print(f'Clusters with Reposts: {clusters_with_reposts:,}')

if total_images > 0:
    repost_rate = (total_reposts / total_images * 100) if total_images > 0 else 0
    print(f'Repost Rate: {repost_rate:.2f}%')

# Top reposted clusters
print('\n' + '-' * 80)
print('TOP 10 MOST REPOSTED IMAGES:')
print('-' * 80)

query = '''
MATCH (c:ImageCluster)
WHERE c.repost_count > 0
OPTIONAL MATCH (c)-[:CANONICAL]->(canonical:ImageFile)
OPTIONAL MATCH (canonical)-[:APPEARED_IN]->(p:Post)
RETURN c.id as cluster_id,
       c.repost_count as reposts,
       c.canonical_sha256 as sha256,
       collect(DISTINCT p.subreddit)[0] as subreddit
ORDER BY c.repost_count DESC
LIMIT 10
'''

result = neo4j.execute_read(query)

if result:
    print('Rank'.ljust(6) + 'Reposts'.ljust(10) + 'Cluster ID'.ljust(38) + 'Subreddit'.ljust(20))
    print('-' * 80)
    for i, record in enumerate(result, 1):
        cluster_id = (record.get('cluster_id') or '')[:36]
        reposts = record.get('reposts') or 0
        subreddit = (record.get('subreddit') or 'N/A')[:18]
        print(str(i).ljust(6) + str(reposts).ljust(10) + cluster_id.ljust(38) + subreddit.ljust(20))
else:
    print('No reposted images found.')

# Detection methods
print('\n' + '-' * 80)
print('DUPLICATE DETECTION METHODS:')
print('-' * 80)

query = '''
MATCH ()-[r:REPOST_OF]->()
WITH r.detected_method as method, count(*) as count
RETURN method, count
ORDER BY count DESC
'''

result = neo4j.execute_read(query)

if result:
    print('Method'.ljust(20) + 'Count'.ljust(10))
    print('-' * 30)
    for record in result:
        method = record.get('method') or 'unknown'
        count = record.get('count', 0)
        print(method.ljust(20) + str(count).ljust(10))
else:
    print('No repost relationships with method tracking found.')

print('\n' + '=' * 80)







