import sys
import os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))
sys.path.insert(0, str(Path(__file__).parent))

from feed.platforms.reddit import RedditAdapter
from datetime import datetime, timedelta

adapter = RedditAdapter()

# Potential subreddits that might have Maddie Ziegler content
subreddits = [
    'MaddieZiegler',
    'Dance',
    'Music',
    'Sia',
    'Dancers',
    'Ballet',
    'Pointe',
    'GirlGroups',
    'Celebs',
    'Maddie'
]

print("=" * 70)
print("SEARCHING FOR MADDIE ZIEGLER CONTENT")
print("=" * 70)

cutoff = datetime.utcnow() - timedelta(days=7)

for sub in subreddits:
    print(f"\n=== r/{sub} ===")
    try:
        posts, after = adapter.fetch_posts(sub, sort='new', limit=50)
        
        maddie_posts = [p for p in posts if 'maddie' in p.title.lower() or 'ziegler' in p.title.lower()]
        
        if maddie_posts:
            print(f"  Found {len(maddie_posts)} Maddie Ziegler posts:")
            for p in maddie_posts[:5]:
                print(f"    [{p.created_utc}] {p.title[:60]}")
        else:
            print(f"  No recent Maddie Ziegler posts (checked {len(posts)} recent posts)")
    except Exception as e:
        print(f"  Error: {e}")

print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)
print("\nRecommended subreddits to monitor for Maddie Ziegler:")
print("  • r/MaddieZiegler - Dedicated subreddit (may be low activity)")
print("  • r/Dance - General dance community")
print("  • r/Dancers - Professional dancers discussion")
print("  • r/Celebs - Celebrity photos including Maddie")
print("  • r/Sia - Fan of Sia (Maddie frequently collaborates)")
