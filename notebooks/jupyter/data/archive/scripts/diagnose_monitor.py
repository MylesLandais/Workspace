#!/usr/bin/env python3
"""Diagnostic script to check imageboard monitoring setup."""

import sys
import subprocess
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

print("=" * 70)
print("IMAGEBOARD MONITOR DIAGNOSTIC")
print("=" * 70)

# 1. Check running processes
print("\n1. CHECKING RUNNING PROCESSES")
print("-" * 70)
result = subprocess.run(
    ["docker", "exec", "jupyter.dev.local", "ps", "aux"],
    capture_output=True,
    text=True
)
monitor_processes = [line for line in result.stdout.split('\n') 
                    if 'monitor_4chan_thread' in line or 'run_4chan_archiver' in line]
if monitor_processes:
    for proc in monitor_processes:
        print(f"  {proc}")
else:
    print("  No monitor processes found")

# 2. Check Neo4j connection
print("\n2. CHECKING NEO4J CONNECTION")
print("-" * 70)
try:
    from feed.storage.neo4j_connection import get_connection
    conn = get_connection()
    print(f"  Connected to: {conn.uri}")
    print(f"  Connection successful!")
    
    # Check for threads in database
    threads_result = conn.execute_read(
        """
        MATCH (t:Thread)
        RETURN t.board, t.thread_id, t.title, t.post_count, t.last_crawled_at
        ORDER BY t.thread_id DESC
        LIMIT 10
        """
    )
    print(f"\n  Threads in database: {len(threads_result)}")
    for thread in threads_result:
        print(f"    /{thread['board']}/{thread['thread_id']}: {thread.get('post_count', 0)} posts")
    
    conn.close()
except Exception as e:
    print(f"  ERROR: {e}")
    print(f"  Neo4j connection failed!")

# 3. Check HTML cache
print("\n3. CHECKING HTML CACHE")
print("-" * 70)
result = subprocess.run(
    ["docker", "exec", "jupyter.dev.local", "ls", "-la", "/home/jovyan/workspaces/cache/imageboard/html/"],
    capture_output=True,
    text=True
)
html_files = [line for line in result.stdout.split('\n') if '.html' in line]
print(f"  HTML files in cache: {len(html_files)}")
for f in html_files:
    print(f"    {f.strip()}")

# 4. Check for specific threads
print("\n4. CHECKING FOR SPECIFIC THREADS")
print("-" * 70)
for thread_id in [944229437, 944234983, 944242003]:
    result = subprocess.run(
        ["docker", "exec", "jupyter.dev.local", "ls", 
         f"/home/jovyan/workspaces/cache/imageboard/html/b_{thread_id}.html"],
        capture_output=True,
        text=True
    )
    if result.returncode == 0:
        print(f"  Thread {thread_id}: HTML file EXISTS")
    else:
        print(f"  Thread {thread_id}: HTML file NOT FOUND")

# 5. Check images cache
print("\n5. CHECKING IMAGES CACHE")
print("-" * 70)
result = subprocess.run(
    ["docker", "exec", "jupyter.dev.local", "find", 
     "/home/jovyan/workspaces/cache/imageboard/images/", "-type", "f"],
    capture_output=True,
    text=True
)
image_files = [line for line in result.stdout.split('\n') if line.strip()]
print(f"  Total images: {len(image_files)}")
for img in image_files[:10]:
    print(f"    {img}")

# 6. Check Neo4j container IP
print("\n6. CHECKING NEO4J CONTAINER IP")
print("-" * 70)
result = subprocess.run(
    ["docker", "inspect", "n4j.jupyter.dev.local", "--format", 
     "{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}"],
    capture_output=True,
    text=True
)
neo4j_ip = result.stdout.strip()
print(f"  Neo4j container IP: {neo4j_ip}")

# Check .env file
env_file = project_root / ".env"
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            if line.startswith("NEO4J_URI="):
                print(f"  NEO4J_URI in .env: {line.strip()}")
                break

print("\n" + "=" * 70)
print("DIAGNOSTIC COMPLETE")
print("=" * 70)