#!/usr/bin/env python3
"""
Universal Feed Reader - Main CLI
Unified interface for managing, fetching, and reading feeds.
"""

import sys
import subprocess
import argparse
import webbrowser
from pathlib import Path

def run_script(script_name, args=None):
    cmd = [sys.executable, script_name]
    if args:
        cmd.extend(args)
    try:
        subprocess.check_call(cmd)
    except subprocess.CalledProcessError as e:
        print(f"Error running {script_name}: {e}")
        sys.exit(e.returncode)

def main():
    parser = argparse.ArgumentParser(description="Universal Feed Reader CLI")
    subparsers = parser.add_subparsers(dest='command', help='Command')

    # Add
    add_parser = subparsers.add_parser('add', help='Add a new feed')
    add_parser.add_argument('url', help='URL to add')

    # List
    subparsers.add_parser('list', help='List subscribed feeds')
    
    # Remove
    remove_parser = subparsers.add_parser('remove', help='Remove a feed')
    remove_parser.add_argument('index', help='Feed index to remove')

    # Update
    subparsers.add_parser('update', help='Fetch new articles and regenerate dashboard')

    # Serve/Browse
    serve_parser = subparsers.add_parser('serve', help='Start local server to browse articles')
    serve_parser.add_argument('--port', type=int, default=8000, help='Port to serve on')

    args = parser.parse_args()

    if args.command == 'add':
        run_script('feed_manager.py', ['add', args.url])
        print("\nTip: Run './reader.py update' to download content for this new feed.")

    elif args.command == 'list':
        run_script('feed_manager.py', ['list'])

    elif args.command == 'remove':
        run_script('feed_manager.py', ['remove', args.index])

    elif args.command == 'update':
        print("📥 Fetching latest articles...")
        run_script('feed_fetcher.py')
        print("\n🔄 Generating dashboard...")
        run_script('generate_dashboard.py')
        print("\n✅ Done! Open 'reader_library/index.html' to browse.")

    elif args.command == 'serve':
        path = Path("reader_library").resolve()
        if not path.exists():
            print("Reader library not found. Run 'update' first.")
            return
            
        print(f"🌍 Serving at http://localhost:{args.port}")
        print("Press Ctrl+C to stop.")
        try:
            # We use python's http.server module directly
            subprocess.check_call([sys.executable, "-m", "http.server", str(args.port), "--directory", "reader_library"])
        except KeyboardInterrupt:
            print("\nServer stopped.")

    else:
        parser.print_help()

if __name__ == "__main__":
    main()
