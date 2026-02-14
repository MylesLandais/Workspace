#!/usr/bin/env python3
"""Simple file server for analytics dashboard using existing port."""
import os
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

class AnalyticsHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(Path(__file__).parent), **kwargs)
    
    def do_GET(self):
        if self.path == '/' or self.path == '':
            self.path = '/analytics.html'
        
        file_path = Path(__file__).parent / self.path[1:]
        
        if file_path.exists() and file_path.is_file():
            with open(file_path, 'rb') as f:
                content = f.read()
            
            self.send_response(200)
            
            if file_path.suffix == '.html':
                self.send_header('Content-type', 'text/html')
            elif file_path.suffix == '.css':
                self.send_header('Content-type', 'text/css')
            elif file_path.suffix == '.js':
                self.send_header('Content-type', 'application/javascript')
            else:
                self.send_header('Content-type', 'text/plain')
            
            self.send_header('Content-length', str(len(content)))
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(content)
        else:
            self.send_error(404, "File not found")
    
    def log_message(self, format, *args):
        pass

if __name__ == "__main__":
    PORT = 8000
    server_address = ('', PORT)
    httpd = HTTPServer(server_address, AnalyticsHandler)
    
    print("=" * 70)
    print("Analytics Dashboard Server")
    print("=" * 70)
    print(f"Serving at: http://0.0.0.0:{PORT}")
    print(f"External access: http://localhost:8000/analytics.html")
    print("Press Ctrl+C to stop")
    print("=" * 70)
    print()
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
        httpd.shutdown()
