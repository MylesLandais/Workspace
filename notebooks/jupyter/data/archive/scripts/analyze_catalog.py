import sys
sys.path.insert(0, '/home/jovyan/workspaces/src')
from feed.platforms.fourchan import ImageboardAdapter

try:
    adapter = ImageboardAdapter(mock=False)
    print(f"Using adapter: {adapter.__class__.__name__}")
    threads = adapter.fetch_threads('b')
except Exception as e:
    print(f"Error fetching threads: {e}")
    threads = []

keywords = ['feet', 'irl', 'girl', 'girls', 'celeb', 'celebs', 'Shota', 'cel', 'panties', 'gooning', 'goon', 'zoomers', 'ecdw', 'cosplay']

matched = []
for t in threads:
    subject = t.get('sub', '').lower() + ' ' + t.get('com', '').lower()
    if any(k in subject for k in keywords):
        matched.append(t)

print(f"Catalog analysis:")
print(f"  Total threads: {len(threads)}")
print(f"  Matched by keywords: {len(matched)}")

print(f"\nCurrently monitoring 17 threads.")

print(f"\nMatched threads NOT being monitored:")
monitored = [944305066, 944330306, 944334107, 944334460, 944335160, 944339094,
             944341070, 944343857, 944345092, 944346714, 944347077, 944347174,
             944347178, 944348635, 944348736, 944350251]

unmonitored = [t for t in matched if t['no'] not in monitored]
for t in unmonitored:
    subject_text = t.get('sub', 'No subject')
    com_text = t.get('com', '')
    full_text = subject_text.lower() + ' ' + com_text.lower()
    matched_keywords = [k for k in keywords if k in full_text]
    print(f"  Thread {t['no']}: {subject_text[:50]}...")
    print(f"    Matches: {matched_keywords}")
