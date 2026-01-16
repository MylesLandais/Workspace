import sys
sys.path.insert(0, '/home/jovyan/workspaces/src')
from feed.storage.neo4j_connection import get_connection

neo4j = get_connection()

# Search for posts containing jordyn, jones, or jj
result = neo4j.execute_read('''
    MATCH (p:Post)-[:POSTED_IN]->(t:Thread {board: "b"})
    WHERE toLower(p.comment) CONTAINS 'jordyn'
       OR toLower(p.comment) CONTAINS 'jones'
       OR toLower(p.comment) CONTAINS 'jj'
    RETURN p.id as post_id, p.post_no as post_no,
           t.thread_id as thread_id, t.title as title,
           p.comment as comment
    LIMIT 20
''')

print('Posts containing "jordyn", "jones", or "jj":')
print(f'Total found: {len(result)}\n')

for r in result:
    title = r.get('title', 'No subject')
    comment_preview = r['comment'][:100] if r['comment'] else 'No comment'
    print(f"Thread {r['thread_id']}: {title[:50]}")
    print(f"  Post {r['post_no']}: {comment_preview}...")
    print()
