#!/usr/bin/env python3
"""
Cleanup old HTML files and provide guidance for viewing imageboard dataset.
"""
import sys
from pathlib import Path

# Directory where old HTML files are stored on host
HOST_HTML_DIR = Path('/home/warby/Workspace/jupyter/cache/imageboard/html')

# Directory where new HTML files are stored inside container
# These are accessible via file:// URLs when opened from Jupyter
CONTAINER_HTML_DIR = Path('/home/jovyan/workspaces/cache/imageboard/html')

def cleanup_old_html_files():
    """Remove old HTML files from host directory that have been superseded."""
    if not HOST_HTML_DIR.exists():
        print("Host HTML directory not found (no cleanup needed)")
        return
    
    # Get list of all HTML files in host directory
    old_files = list(HOST_HTML_DIR.glob('*.html'))
    if not old_files:
        print("No HTML files found in host directory")
        return
    
    print(f"Found {len(old_files)} HTML files in host directory")
    
    # Count how many of these are older than container's files
    # We'll check if files exist in container directory to identify which are old
    new_files = list(CONTAINER_HTML_DIR.glob('*.html')) if CONTAINER_HTML_DIR.exists() else []
    new_file_names = {f.name for f in new_files}
    
    removed = 0
    kept = 0
    
    for old_file in old_files:
        if old_file.name in new_file_names:
            # This is an old file that has been superseded
            try:
                old_file.unlink()
                removed += 1
                print(f"  Removed old file: {old_file.name}")
            except Exception as e:
                print(f"  Error removing {old_file.name}: {e}")
        else:
            kept += 1
    
    print(f"\nSummary: Removed {removed} old files, kept {kept} current files")

def main():
    print("=" * 70)
    print("IMAGEBOARD HTML CLEANUP")
    print("=" * 70)
    print(f"Host directory: {HOST_HTML_DIR}")
    print(f"Container directory: {CONTAINER_HTML_DIR}")
    print()
    
    cleanup_old_html_files()
    
    print("\n" + "=" * 70)
    print("VIEWING HTML FILES")
    print("=" * 70)
    print("\nHTML files in container are accessible from Jupyter via file:// URLs")
    print("Example: file:///home/jovyan/workspaces/cache/imageboard/html/b_944476821.html")
    print("\nOr open the imageboard_dataset_explorer.ipynb notebook in Jupyter")
    print("to explore the dataset with images and search.")
    print("\n" + "=" * 70)
    print("COMPLETE")

if __name__ == "__main__":
    main()
