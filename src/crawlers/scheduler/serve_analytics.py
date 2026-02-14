#!/usr/bin/env python3
"""Simple HTTP server for analytics dashboard."""
import http.server
import socketserver
import webbrowser
from pathlib import Path
import sys

PORT = 8889

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(Path(__file__).parent), **kwargs)

    def do_GET(self):
        if self.path == '/' or self.path == '':
            self.path = '/analytics.html'
        return super().do_GET()

    def end_headers(self):
        # Add CORS headers
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

def start_server():
    """Start the analytics web server."""
    analytics_path = Path(__file__).parent / 'analytics.html'
    
    if not analytics_path.exists():
        print(f"Error: analytics.html not found at {analytics_path}")
        print("Run: python generate_analytics.py")
        sys.exit(1)
    
    handler = MyHTTPRequestHandler
    
    with socketserver.TCPServer(("", PORT), handler) as httpd:
        print(f"=" * 70)
        print(f"Analytics Dashboard Server")
        print(f"=" * 70)
        print(f"Serving analytics.html at http://localhost:{PORT}")
        print(f"Press Ctrl+C to stop")
        print(f"=" * 70)
        print()
        
        # Open browser
        try:
            webbrowser.open(f'http://localhost:{PORT}')
        except:
            print("Could not auto-open browser. Please visit manually.")
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")

if __name__ == "__main__":
    start_server()
