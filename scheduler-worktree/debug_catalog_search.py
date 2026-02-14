import sys
sys.path.insert(0, '/home/jovyan/workspaces/src')
from feed.platforms.fourchan import ImageboardAdapter
from feed.storage.neo4j_connection import get_connection

adapter = ImageboardAdapter(mock=False)
threads = adapter.fetch_threads('b')

print(f"Catalog returned {len(threads)} threads")
print()

# Search for JJ threads
jj_threads = []
for t in threads:
    subject = t.get('sub', '').lower()
    comment = t.get('com', '').lower()
    if 'jj' in subject or 'jj' in comment or 'jordyn' in subject or 'jordyn' in comment:
        jj_threads.append(t)

print(f"Threads matching JJ/jordyn: {len(jj_threads)}")
print()

for t in jj_threads[:10]:
    print(f"Thread {t['no']}:")
    print(f"  Subject: {t.get('sub', 'No subject')}")
    print(f"  Comment: {t.get('com', '')[:100]}")
    print()

# Check if thread 944335888 is in catalog
thread_944335888 = [t for t in threads if t['no'] == 944335888]
print(f"Thread 944335888 in catalog: {len(thread_944335888) > 0}")
if thread_944335888:
    t = thread_944335888[0]
    print(f"Subject: {t.get('sub', 'No subject')}")
    print(f"Comment: {t.get('com', '')[:100]}")
