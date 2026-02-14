#!/usr/bin/env python3
"""Periodic imageboard catalog poller with random intervals."""

import sys
import time
import random
import subprocess
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

# Poll every 2-4 hours (7200-14400 seconds)
POLL_INTERVAL_MIN = 7200
POLL_INTERVAL_MAX = 14400

def get_random_interval() -> int:
    """Get a random interval between min and max."""
    return random.randint(POLL_INTERVAL_MIN, POLL_INTERVAL_MAX)

def run_monitor_orchestrator():
    """Run the start_imageboard_monitors.py script."""
    print("=" * 70)
    print("RUNNING MONITOR ORCHESTRATOR")
    print("=" * 70)
    
    script_path = project_root / "start_imageboard_monitors.py"
    cmd = [sys.executable, str(script_path)]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        return result.returncode == 0
    except Exception as e:
        print(f"Error running orchestrator: {e}")
        return False

def main():
    """Main polling loop."""
    print("=" * 70)
    print("PERIODIC IMAGEBOARD CATALOG POLLER")
    print("=" * 70)
    print(f"Poll interval: {POLL_INTERVAL_MIN}-{POLL_INTERVAL_MAX} seconds ({POLL_INTERVAL_MIN/60:.0f}-{POLL_INTERVAL_MAX/60:.0f} min)")
    print()
    print("This will periodically scan the catalog and start monitors for matching threads.")
    print("Press Ctrl+C to stop.")
    print("=" * 70)
    print()
    
    try:
        # Initial run
        print("\nPerforming initial catalog scan...")
        run_monitor_orchestrator()
        
        # Polling loop
        while True:
            interval = get_random_interval()
            hours = interval // 3600
            minutes = (interval % 3600) // 60
            
            print(f"\nNext scan in {hours}h {minutes}m ({interval}s)...")
            print(f"Waiting...")
            
            # Sleep with interruption check
            sleep_remaining = interval
            while sleep_remaining > 0:
                sleep_time = min(10, sleep_remaining)
                time.sleep(sleep_time)
                sleep_remaining -= sleep_time
            
            # Run orchestrator
            print("\nRunning catalog scan...")
            run_monitor_orchestrator()
    
    except KeyboardInterrupt:
        print("\n\nStopped by user.")
        print("Note: Running monitors will continue. Use 'pkill -f monitor_imageboard_thread.py' to stop all.")
        return 0
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
