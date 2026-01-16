import os
from feed.storage.neo4j_connection import get_connection

# Get Neo4j connection
neo4j = get_connection()
print(f"Connected to Neo4j: {neo4j.uri}")

# Find the specific post
print("\n=== Post 1q9btf7 ====")
result = neo4j.execute_read("""
MATCH (p:Post {id: $id})
RETURN p.title, p.url, p.author, p.score, p.created_utc, p.subreddit
""", parameters={"id": "1q9btf7"})

for record in result:
    print(f"Title: {record['p.title']}")
    print(f"URL: {record['p.url']}")
    print(f"Author: {record['p.author']}")
    print(f"Score: {record['p.score']}")
    print(f"Created: {record['p.created_utc']}")
    print(f"Subreddit: {record['p.subreddit']}")

# Find all posts mentioning Maddie Ziegler
print("\n=== All Maddie Ziegler posts ====")
result2 = neo4j.execute_read("""
MATCH (p:Post)
WHERE toLower(p.title) CONTAINS toLower('Maddie Ziegler')
RETURN p.title, p.subreddit, p.url, p.id, p.created_utc
ORDER BY p.created_utc DESC
""")

for record in result2:
    print(f"r/{record['p.subreddit']} - {record['p.title'][:60]}...")

# Find unique subreddits with Maddie Ziegler posts
print("\n=== Subreddits with Maddie Ziegler ====")
result3 = neo4j.execute_read("""
MATCH (p:Post)
WHERE toLower(p.title) CONTAINS toLower('Maddie Ziegler')
RETURN DISTINCT p.subreddit, count(p) as post_count
ORDER BY post_count DESC
""")

for record in result3:
    print(f"r/{record['p.subreddit']} - {record['post_count']} posts")

neo4j.close()
