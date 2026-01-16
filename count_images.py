import json
import os
import sys

def count_unique_images():
    THREADS = [944499878, 944501761, 944456488, 944473096, 944487355, 944502496, 944501078, 944504486]
    # This path is relative to the container's workspace mount
    CACHE_DIR = '/home/jovyan/workspaces/cache/imageboard/threads/b/'
    unique_images = set()

    for t in THREADS:
        path = os.path.join(CACHE_DIR, str(t), 'thread.json')
        if os.path.exists(path):
            try:
                with open(path, 'r') as f:
                    data = json.load(f)
                    for post in data.get('posts', []):
                        if 'local_image' in post:
                            unique_images.add(post['local_image'])
            except Exception as e:
                # This could mean the thread is actively being written by the worker
                # print(f"Error reading {t}: {e}")
                pass

    print(f"Unique Images Referenced in Polled Threads: {len(unique_images)}")
    # We cannot reliably check the creation date of these files to isolate 'today's' downloads,
    # but this total gives the max contribution.

if __name__ == "__main__":
    count_unique_images()
