"""Organize existing imageboard images into board/thread structure.

This script reorganizes images from the flat structure to the new organized structure
based on board and thread_id from Neo4j.
"""

import sys
from pathlib import Path
from typing import Dict, List
import shutil

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "src"))

from feed.storage.neo4j_connection import get_connection


def get_image_mappings(neo4j) -> Dict[str, Dict[str, str]]:
    """
    Get mappings of image hashes to board/thread from Neo4j.
    
    Returns:
        Dictionary mapping image_hash -> {board, thread_id, image_path}
    """
    query = """
    MATCH (p:Post)
    WHERE p.image_hash IS NOT NULL AND p.image_path IS NOT NULL
    MATCH (p)-[:POSTED_IN]->(t:Thread)
    RETURN p.image_hash as hash,
           t.board as board,
           t.thread_id as thread_id,
           p.image_path as path
    """
    
    result = neo4j.execute_read(query)
    mappings = {}
    
    for record in result:
        image_hash = record.get("hash")
        if image_hash:
            mappings[image_hash] = {
                "board": record.get("board"),
                "thread_id": str(record.get("thread_id")),
                "path": record.get("path"),
            }
    
    return mappings


def organize_images(
    flat_images_dir: Path,
    organized_images_dir: Path,
    mappings: Dict[str, Dict[str, str]],
    dry_run: bool = False
) -> Dict[str, int]:
    """
    Organize images from flat structure to board/thread structure.
    
    Args:
        flat_images_dir: Directory with flat image structure
        organized_images_dir: Base directory for organized structure
        mappings: Hash to board/thread mappings
        dry_run: If True, don't actually move files
        
    Returns:
        Statistics dictionary
    """
    stats = {
        "organized": 0,
        "skipped": 0,
        "errors": 0,
        "not_found": 0,
    }
    
    # Find all image files in flat directory
    image_files = list(flat_images_dir.glob("*.*"))
    image_files = [f for f in image_files if f.suffix.lower() in [".jpg", ".png", ".gif", ".webm"]]
    
    print(f"Found {len(image_files)} image files to organize")
    print(f"Mappings available: {len(mappings)}")
    print()
    
    for image_file in image_files:
        # Extract hash from filename (assuming format: {hash}.{ext})
        hash_part = image_file.stem
        
        if hash_part not in mappings:
            stats["not_found"] += 1
            continue
        
        mapping = mappings[hash_part]
        board = mapping["board"]
        thread_id = mapping["thread_id"]
        
        # Create organized directory structure
        thread_dir = organized_images_dir / board / thread_id
        if not dry_run:
            thread_dir.mkdir(parents=True, exist_ok=True)
        
        # Destination path
        dest_path = thread_dir / image_file.name
        
        try:
            if dest_path.exists():
                # Already organized, skip
                stats["skipped"] += 1
                continue
            
            if not dry_run:
                # Move file to organized location
                shutil.move(str(image_file), str(dest_path))
                
                # Create symlink in flat directory for backward compatibility
                try:
                    image_file.symlink_to(dest_path.relative_to(flat_images_dir))
                except (OSError, FileExistsError):
                    pass
            
            stats["organized"] += 1
            
            if stats["organized"] % 10 == 0:
                print(f"Organized {stats['organized']} images...")
                
        except Exception as e:
            print(f"Error organizing {image_file.name}: {e}")
            stats["errors"] += 1
    
    return stats


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Organize imageboard images into board/thread structure"
    )
    parser.add_argument(
        "--cache-dir",
        type=Path,
        default=Path("/home/jovyan/workspace/cache/imageboard"),
        help="Cache directory (default: /home/jovyan/workspace/cache/imageboard)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Don't actually move files, just show what would be done"
    )
    
    args = parser.parse_args()
    
    cache_dir = args.cache_dir
    flat_images_dir = cache_dir / "images"
    organized_images_dir = cache_dir / "images_organized"
    
    if not flat_images_dir.exists():
        print(f"Error: Images directory not found: {flat_images_dir}")
        return 1
    
    print("=" * 70)
    print("IMAGEBOARD IMAGE ORGANIZER")
    print("=" * 70)
    print(f"Flat images directory: {flat_images_dir}")
    print(f"Organized images directory: {organized_images_dir}")
    print(f"Dry run: {args.dry_run}")
    print()
    
    # Connect to Neo4j
    print("Connecting to Neo4j...")
    try:
        # Try to find .env file
        env_paths = [
            cache_dir.parent / ".env",
            Path("/home/jovyan/workspace/.env"),
            Path("/home/jovyan/workspaces/.env"),
            Path.home() / "Workspace" / "jupyter" / ".env",
        ]
        
        env_path = None
        for path in env_paths:
            if path.exists():
                env_path = path
                break
        
        if env_path:
            from feed.storage.neo4j_connection import Neo4jConnection
            neo4j = Neo4jConnection(env_path=env_path)
        else:
            neo4j = get_connection()
        
        print(f"Connected to: {neo4j.uri}")
    except Exception as e:
        print(f"Error connecting to Neo4j: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    # Get image mappings
    print("Fetching image mappings from Neo4j...")
    mappings = get_image_mappings(neo4j)
    print(f"Found {len(mappings)} image mappings")
    print()
    
    if not mappings:
        print("No image mappings found in database. Make sure threads have been processed.")
        return 1
    
    # Organize images
    print("Organizing images...")
    stats = organize_images(
        flat_images_dir,
        organized_images_dir,
        mappings,
        dry_run=args.dry_run
    )
    
    print()
    print("=" * 70)
    print("ORGANIZATION COMPLETE")
    print("=" * 70)
    print(f"Organized: {stats['organized']}")
    print(f"Skipped (already exists): {stats['skipped']}")
    print(f"Not found in mappings: {stats['not_found']}")
    print(f"Errors: {stats['errors']}")
    
    if args.dry_run:
        print()
        print("This was a dry run. Run without --dry-run to actually organize files.")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

