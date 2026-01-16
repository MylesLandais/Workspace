#!/usr/bin/env python3
"""Start gallery server with error handling."""

import sys
import subprocess
import time
from pathlib import Path


def check_port(port: int) -> bool:
    """Check if port is in use."""
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('localhost', port))
            return False
        except:
            return True


def start_server(port: int = 8001):
    """Start gallery server."""
    print("=" * 60)
    print("Gallery Server Startup")
    print("=" * 60)
    
    # Check port
    if check_port(port):
        print(f"✗ Port {port} is already in use")
        print(f"  Try using a different port:")
        print(f"  cd gallery/api && python main_standalone.py")
        print("  Then modify the code to use a different port")
        return False
    
    print(f"✓ Port {port} is available")
    
    # Check directories
    cache_dir = Path.home() / ".cache" / "gallery"
    if not cache_dir.exists():
        cache_dir.mkdir(parents=True, exist_ok=True)
        print(f"✓ Created cache directory: {cache_dir}")
    else:
        print(f"✓ Cache directory exists: {cache_dir}")
    
    # Check dependencies
    print("\nChecking dependencies...")
    dependencies = [
        ("fastapi", "fastapi"),
        ("uvicorn", "uvicorn"),
    ]
    
    missing = []
    for name, package in dependencies:
        try:
            __import__(name)
            print(f"  ✓ {name}")
        except ImportError:
            print(f"  ✗ {name} (not installed)")
            missing.append(package)
    
    if missing:
        print(f"\n✗ Missing dependencies: {', '.join(missing)}")
        print("Install with:")
        print(f"  pip install {' '.join(missing)}")
        return False
    
    print("\n✓ All dependencies installed")
    
    # Start server
    print("\nStarting server...")
    print(f"  URL: http://localhost:{port}")
    print(f"  Health: http://localhost:{port}/health")
    print("\nPress Ctrl+C to stop")
    print("=" * 60)
    
    try:
        import uvicorn
        from gallery.api.main_standalone import app
        
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=port,
            log_level="info",
            access_log=True
        )
    except KeyboardInterrupt:
        print("\n\nServer stopped by user")
        return True
    except Exception as e:
        print(f"\n✗ Error starting server: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    port = 8001
    
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print(f"Invalid port: {sys.argv[1]}")
            sys.exit(1)
    
    success = start_server(port)
    sys.exit(0 if success else 1)
