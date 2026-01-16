#!/usr/bin/env python3
"""Setup script for gallery system."""

import subprocess
import sys
from pathlib import Path


def run_command(cmd: str, description: str) -> bool:
    """Run command and return success status."""
    print(f"\n{description}...")
    try:
        subprocess.run(cmd, shell=True, check=True)
        print(f"✓ {description} complete")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ {description} failed: {e}")
        return False


def main():
    """Setup gallery system."""
    print("=" * 60)
    print("Gallery System Setup")
    print("=" * 60)
    
    # Check Python version
    if sys.version_info < (3, 9):
        print("✗ Python 3.9+ required")
        return False
    
    print(f"✓ Python {sys.version_info.major}.{sys.version_info.minor}")
    
    # Install Python dependencies
    dependencies = [
        "fastapi",
        "uvicorn[standard]",
        "aiofiles",
        "requests",
        "Pillow",
    ]
    
    deps_str = " ".join(dependencies)
    if not run_command(f"pip install {deps_str}", "Installing Python dependencies"):
        return False
    
    # Create cache directories
    cache_dirs = [
        Path.home() / ".cache" / "gallery" / "html",
        Path.home() / ".cache" / "gallery" / "thumbnails",
    ]
    
    for dir_path in cache_dirs:
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"✓ Created directory: {dir_path}")
    
    # Setup static files
    static_dir = Path(__file__).parent / "frontend" / "scripts"
    if static_dir.exists():
        print(f"✓ Static files directory: {static_dir}")
    
    print("\n" + "=" * 60)
    print("Setup Complete!")
    print("=" * 60)
    print("\nTo start the gallery server:")
    print("  cd gallery/api")
    print("  python main.py")
    print("\nThen open http://localhost:8001 in your browser")
    print("\nFeatures:")
    print("  • Browse catalogues by source (subreddit, channel, etc.)")
    print("  • View cached HTML with custom styling")
    print("  • Grid and list view modes")
    print("  • Search functionality")
    print("  • NSFW filtering")
    print("  • Cached-only filtering")
    print("  • Responsive design")
    print("\nCache locations:")
    print(f"  • HTML: {cache_dirs[0]}")
    print(f"  • Thumbnails: {cache_dirs[1]}")
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
