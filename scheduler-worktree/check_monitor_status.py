"""Check status of all monitored threads and image downloads."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "src"))

from feed.storage.neo4j_connection import get_connection

def main():
    print("=" * 70)
    print("MONITOR STATUS CHECK")
    print("=" * 70)
    
    conn = get_connection()
    
    # Get all threads
    threads_result = conn.execute_read(
        """
        MATCH (t:Thread)
        RETURN t.board as board,
               t.thread_id as thread_id,
               t.title as title,
               t.post_count as post_count,
               t.last_crawled_at as last_crawled
        ORDER BY t.thread_id DESC
        """
    )
    
    print(f"\nFound {len(threads_result)} thread(s) in database:\n")
    
    for thread in threads_result:
        thread_id = thread['thread_id']
        board = thread['board']
        
        # Get image stats for this thread
        image_result = conn.execute_read(
            """
            MATCH (t:Thread {board: $board, thread_id: $thread_id})<-[:POSTED_IN]-(p:Post)
            WHERE p.image_url IS NOT NULL
            WITH count(p) as total_images,
                 count(CASE WHEN p.image_hash IS NOT NULL THEN 1 END) as downloaded_images
            RETURN total_images, downloaded_images
            """,
            parameters={"board": board, "thread_id": thread_id}
        )
        
        total_images = image_result[0]['total_images'] if image_result else 0
        downloaded = image_result[0]['downloaded_images'] if image_result else 0
        
        print(f"Thread /{board}/{thread_id}: {thread.get('title', 'N/A')}")
        print(f"  Posts: {thread.get('post_count', 0)}")
        print(f"  Images: {total_images} total, {downloaded} downloaded ({downloaded}/{total_images})")
        if total_images > 0:
            pct = (downloaded / total_images * 100) if total_images > 0 else 0
            print(f"  Download status: {pct:.1f}%")
        print()
    
    # Check file system
    images_dir = Path("/home/jovyan/workspace/cache/imageboard/images")
    if images_dir.exists():
        image_files = list(images_dir.glob("*"))
        total_size = sum(f.stat().st_size for f in image_files if f.is_file())
        print("=" * 70)
        print("FILE SYSTEM")
        print("=" * 70)
        print(f"Images directory: {images_dir}")
        print(f"Total cached images: {len(image_files)}")
        print(f"Total size: {total_size:,} bytes ({total_size / 1024 / 1024:.2f} MB)")
        print(f"Host path: /home/warby/Workspace/jupyter/cache/imageboard/images/")
    
    # Check running monitors
    print("\n" + "=" * 70)
    print("RUNNING MONITORS")
    print("=" * 70)
    print("(Check with: docker exec jupyter ps aux | grep monitor_4chan_thread)")
    
    conn.close()

if __name__ == "__main__":
    main()






