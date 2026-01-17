"""
Simple static file server for frontend testing
Run this to serve the index.html file
"""

from http.server import HTTPServer, SimpleHTTPRequestHandler
import os

class CORSRequestHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

if __name__ == '__main__':
    # Change to frontend directory
    os.chdir(os.path.join(os.path.dirname(__file__), '..', 'frontend'))
    
    port = 3000
    server = HTTPServer(('localhost', port), CORSRequestHandler)
    print(f'🚀 Frontend server running at http://localhost:{port}')
    print(f'📂 Serving files from: {os.getcwd()}')
    print(f'Open http://localhost:{port} in your browser')
    print('Press Ctrl+C to stop')
    
    server.serve_forever()
