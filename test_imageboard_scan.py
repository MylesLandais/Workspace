"""Simple test script to scan imageboard for 'irl' threads."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from feed.platforms.fourchan import ImageboardAdapter


def test_scan_irl_threads():
    """Test scanning /b/ board for 'irl' threads."""
    print("=" * 70)
    print("IMAGEBOARD IRL THREAD SCANNER TEST")
    print("=" * 70)
    print()
    
    # Initialize adapter with 'irl' keyword filtering
    imageboard = ImageboardAdapter(
        delay_min=1.0,  # Faster for testing
        delay_max=2.0,
        keywords=["irl"],
        mock=False
    )
    
    # Test keyword matching
    print("Testing keyword matching:")
    test_cases = [
        ("IRL fap 6", True),
        ("irl thread", True),
        ("GIRL thread", False),  # Should NOT match
        ("twirl dance", False),  # Should NOT match
        ("irl!", True),  # Should match (word boundary at punctuation)
    ]
    
    for title, should_match in test_cases:
        matches = imageboard._matches_keywords(title)
        status = "✓" if matches == should_match else "✗"
        print(f"  {status} '{title}' -> {matches} (expected {should_match})")
    
    print()
    
    # Fetch threads from /b/ board
    print("Fetching threads from /b/ board...")
    print()
    
    threads = imageboard.fetch_threads("b")
    
    print(f"Found {len(threads)} threads matching 'irl' keyword")
    print()
    
    if threads:
        print("Sample threads found:")
        for i, thread in enumerate(threads[:10], 1):
            thread_id = thread.get("no", "N/A")
            subject = thread.get("sub", "") or "No subject"
            replies = thread.get("replies", 0)
            images = thread.get("images", 0)
            
            print(f"  {i}. Thread {thread_id}: {subject[:60]}")
            print(f"     Replies: {replies}, Images: {images}")
            print()
    else:
        print("No threads found matching 'irl' keyword")
    
    print("=" * 70)


if __name__ == "__main__":
    try:
        test_scan_irl_threads()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Exiting...")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()





