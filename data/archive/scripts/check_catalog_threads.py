import sys
sys.path.insert(0, '/home/jovyan/workspaces/src')
from feed.platforms.fourchan import ImageboardAdapter
from feed.storage.neo4j_connection import get_connection

adapter = ImageboardAdapter(mock=False)
threads = adapter.fetch_threads('b')

# Check for IRL threads
irl_threads = [t for t in threads if 'irl' in t.get('sub', '').lower() + t.get('com', '').lower()]
print('IRL threads in catalog:')
for t in irl_threads:
    print(f"  Thread {t['no']}: {t.get('sub', 'No subject')} - {t.get('resto', 0)} replies")

# Check for celeb threads
celeb_threads = [t for t in threads if any(k in t.get('sub', '').lower() + t.get('com', '').lower() for k in ['celeb', 'celebs'])]
print('\nCeleb threads in catalog:')
for t in celeb_threads[:5]:
    print(f"  Thread {t['no']}: {t.get('sub', 'No subject')}")

# Check database status
neo4j = get_connection()
thread_ids = [944347077, 944350251, 944351708]
result = neo4j.execute_read('''
    MATCH (t:Thread) WHERE t.thread_id IN $thread_ids
    RETURN t.thread_id, t.title, t.post_count, t.last_crawled_at
    ORDER BY t.thread_id
''', parameters={"thread_ids": thread_ids})

print('\nDatabase status:')
for r in result:
    print(f"  Thread {r['t.thread_id']}: {r.get('t.title', 'No subject')[:50]} - {r['t.post_count']} posts")
    print(f"    Last crawled: {r['t.last_crawled_at']}")
