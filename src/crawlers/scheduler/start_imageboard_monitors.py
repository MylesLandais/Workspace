#!/usr/bin/env python3
"""Find and monitor imageboard threads matching specific keywords."""

import sys
import subprocess
import signal
import os
from pathlib import Path
from typing import List, Dict, Any

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from feed.platforms.fourchan import ImageboardAdapter

# Keywords to search for
KEYWORDS = ["JJ", "IRL", "build", "cel", "celeb", "feet", "face", "faces", "insta", "tiktok", "vsco", "panties", "gooning", "goon", "zoomers", "ecdw", "cosplay"]
BOARD = "b"
MONITOR_INTERVAL = 600  # 10 minutes


def find_matching_threads() -> List[Dict[str, Any]]:
    """Fetch catalog and return threads matching keywords."""
    print(f"Fetching /{BOARD}/ catalog...")
    
    imageboard = ImageboardAdapter(
        delay_min=2.0,
        delay_max=5.0,
        keywords=KEYWORDS,
        mock=False
    )
    
    threads = imageboard.fetch_threads(BOARD)
    print(f"Found {len(threads)} threads matching keywords: {KEYWORDS}")
    
    return threads


def start_thread_monitor(thread_id: int, subject: str):
    """Start monitoring a thread in the background."""
    thread_url = f"https://boards.4chan.org/{BOARD}/thread/{thread_id}"
    
    print(f"Starting monitor for thread {thread_id}: {subject[:60]}...")
    
    # Build command
    script_path = project_root / "monitor_imageboard_thread.py"
    cmd = [
        sys.executable,
        str(script_path),
        thread_url,
        "--interval", str(MONITOR_INTERVAL),
        "--cache-dir", str(project_root / "cache" / "imageboard"),
    ]
    
    # Start in background (detached)
    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True
        )
        print(f"  -> Monitor started (PID: {process.pid})")
        return process.pid
    except Exception as e:
        print(f"  -> Error starting monitor: {e}")
        return None


def main():
    """Main entry point."""
    print("=" * 70)
    print("IMAGEBOARD THREAD MONITOR ORCHESTRATOR")
    print("=" * 70)
    print(f"Board: /{BOARD}/")
    print(f"Keywords: {KEYWORDS}")
    print(f"Monitor interval: {MONITOR_INTERVAL} seconds ({MONITOR_INTERVAL / 60:.1f} minutes)")
    print()
    
    # Find matching threads
    threads = find_matching_threads()
    
    if not threads:
        print("No threads found. Exiting.")
        return
    
    print("\n" + "=" * 70)
    print("STARTING MONITORS")
    print("=" * 70)
    
    # Start monitors for each thread
    started_pids = []
    for thread_data in threads:
        thread_id = thread_data.get("no")
        subject = thread_data.get("sub", "") or "No subject"
        
        pid = start_thread_monitor(thread_id, subject)
        if pid:
            started_pids.append(pid)
    
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Threads found: {len(threads)}")
    print(f"Monitors started: {len(started_pids)}")
    print(f"Monitor PIDs: {started_pids}")
    print()
    print("Monitors are running in the background.")
    print("To stop all monitors, run: pkill -f monitor_imageboard_thread.py")
    print()


if __name__ == "__main__":
    main()
