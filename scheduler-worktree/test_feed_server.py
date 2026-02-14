#!/usr/bin/env python3
"""Test the feed monitor web server."""

import sys
import time
import subprocess
from pathlib import Path

def test_server():
    """Test if server is running and responding."""
    import requests
    
    try:
        # Test stats endpoint
        response = requests.get("http://localhost:8000/api/stats", timeout=5)
        if response.status_code == 200:
            stats = response.json()
            print("✓ Server is running!")
            print(f"  Total Posts: {stats.get('total_posts', 0)}")
            print(f"  Subreddits: {stats.get('subreddits', 0)}")
            print(f"  Users: {stats.get('users', 0)}")
            return True
        else:
            print(f"✗ Server returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("✗ Server is not running or not accessible")
        print("  Start it with: docker exec -w /home/jovyan/workspace jupyter python3 src/feed/web/server.py")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

if __name__ == "__main__":
    print("Testing Feed Monitor Web Server...")
    print("-" * 60)
    
    if test_server():
        print("\n✓ Server is working correctly!")
        print("\nAccess the web interface at: http://localhost:8000")
        print("API documentation at: http://localhost:8000/docs")
    else:
        print("\n✗ Server test failed")
        sys.exit(1)








