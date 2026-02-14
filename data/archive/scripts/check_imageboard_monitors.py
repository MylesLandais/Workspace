#!/usr/bin/env python3
"""Check status of running imageboard monitors."""

import sys
import subprocess
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from feed.storage.neo4j_connection import get_connection


def check_monitors():
    """Check running monitor processes."""
    result = subprocess.run(
        ["ps", "aux"],
        capture_output=True,
        text=True
    )
    
    monitor_lines = [
        line for line in result.stdout.split('\n')
        if 'monitor_imageboard_thread.py' in line
    ]
    
    return monitor_lines


def check_database():
    """Check what threads are in the database."""
    neo4j = get_connection()
    
    # Get all threads
    result = neo4j.execute_read("""
        MATCH (t:Thread {board: "b"})
        WHERE t.last_crawled_at > datetime() - duration('P1D')
        RETURN t.thread_id, t.subject, t.post_count, t.last_crawled_at
        ORDER BY t.last_crawled_at DESC
        LIMIT 20
    """)
    
    return result


def main():
    """Main entry point."""
    print("=" * 70)
    print("IMAGEBOARD MONITOR STATUS")
    print("=" * 70)
    print()
    
    # Check running monitors
    monitor_lines = check_monitors()
    print(f"Running monitors: {len(monitor_lines)}")
    print()
    
    # Check database
    print("Recently crawled threads (last 24 hours):")
    print("-" * 70)
    
    threads = check_database()
    for thread in threads:
        thread_id = thread['t.thread_id']
        subject = thread.get('t.subject', 'No subject')
        post_count = thread.get('t.post_count', 0)
        crawled_at = thread.get('t.last_crawled_at', 'Unknown')
        
        print(f"Thread {thread_id}:")
        print(f"  Subject: {subject}")
        print(f"  Posts: {post_count}")
        print(f"  Last crawled: {crawled_at}")
        print()
    
    print("=" * 70)
    print()
    print("To stop all monitors, run:")
    print("  docker compose exec jupyterlab pkill -f monitor_imageboard_thread.py")
    print()


if __name__ == "__main__":
    main()
