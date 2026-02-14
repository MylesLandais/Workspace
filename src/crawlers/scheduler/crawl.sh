
#!/bin/bash
python3 -c "
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd() / 'src'))
from feed.platforms.reddit import RedditAdapter
from feed.storage.neo4j_connection import get_connection
from feed.storage.thread_storage import store_thread_from_crawl_result

# Initialize RedditAdapter
reddit = RedditAdapter(mock=False, delay_min=2.0, delay_max=5.0)

# Fetch the thread
permalink = 'https://www.reddit.com/r/TaylorSwiftPictures/comments/1pxtr93/taylors_workout/'
post, comments, raw_post_data = reddit.fetch_thread(permalink)

if not post:
    print(f'ERROR: Failed to fetch thread {permalink}')
    exit(1)

# Process the results
result = {
    'success': True,
    'permalink': permalink,
    'post_id': post.id,
    'timestamp': '2025-12-29T03:00:00Z',
    'post': {
        'id': post.id,
        'title': post.title,
        'author': post.author,
        'subreddit': post.subreddit,
        'created_utc': post.created_utc.isoformat(),
        'score': post.score,
        'num_comments': post.num_comments,
        'upvote_ratio': post.upvote_ratio,
        'selftext': post.selftext,
        'url': post.url,
        'permalink': post.permalink,
    },
    'images': [],
    'comments': [],
    'op_comments': [],
}

# Extract images from the post
if raw_post_data:
    images = reddit.extract_all_images(post, raw_post_data)
    for img_url in images:
        result['images'].append({
            'url': img_url,
            'source': 'post',
        })

# Extract comments
if comments:
    for comment in comments:
        result['comments'].append({
            'id': comment.id,
            'body': comment.body,
            'author': comment.author,
            'created_utc': comment.created_utc.isoformat(),
            'score': comment.score,
            'ups': comment.ups,
            'downs': comment.downs,
            'depth': comment.depth,
            'is_submitter': comment.is_submitter,
            'parent_id': comment.parent_id,
            'permalink': comment.permalink,
        })
        if comment.is_submitter:
            result['op_comments'].append(result['comments'][-1])

# Store the thread in Neo4j
neo4j = get_connection()
store_thread_from_crawl_result(neo4j, result)

# Create the Person node and the MENTIONS relationship
query = '''
MERGE (p:Person {name: "Taylor Swift"})
ON CREATE SET p:Actor, p:GenericAbstraction
WITH p
MATCH (post:Post {id: \$post_id})
MERGE (post)-[:MENTIONS]->(p)
'''
neo4j.execute_write(query, parameters={'post_id': post.id})

print(f'Successfully crawled and stored thread {post.id}')
"
