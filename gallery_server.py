from flask import Flask, send_from_directory, request
import webbrowser
import argparse
import socket
from pathlib import Path
import os
import json


class GalleryServer:
    def __init__(self, gallery_dir="./gallery_output", port=8000, host='0.0.0.0'):
        self.gallery_dir = Path(gallery_dir)
        self.port = port
        self.host = host
        self.likes_file = Path(os.getcwd()) / 'gallery_output' / 'likes.json'
        self.app = Flask(__name__)
        
        # Configure route
        @self.app.route('/<path:path>')
        def serve_files(path):
            return send_from_directory(self.gallery_dir, path)
            
        @self.app.route('/')
        def serve_root():
            return send_from_directory(self.gallery_dir, 'index.html')
        
        @self.app.get('/likes')
        def get_likes():
            with self.likes_file.open("r") as f:
                print(json.load(f))
            with self.likes_file.open("r") as f:
                return json.load(f)
        
        @self.app.post('/save-likes')
        def save_likes():
            with self.likes_file.open("r") as f:
                likes = json.load(f)

            incoming = request.get_json()

            for key, value in incoming.items():
                likes[key] = value

            with self.likes_file.open("w") as f:
                json.dump(likes, f)
            return {}

    def get_ip_addresses(self):
        """Get all network interfaces IP addresses."""
        addresses = []
        try:
            # Get all network interfaces
            interfaces = socket.getaddrinfo(
                host=socket.gethostname(),
                port=None,
                family=socket.AF_INET
            )
            # Extract unique IP addresses
            addresses = sorted(set(item[4][0] for item in interfaces))
        except Exception as e:
            print(f"Warning: Could not get network interfaces: {e}")
        
        # Always include localhost
        if '127.0.0.1' not in addresses:
            addresses.insert(0, '127.0.0.1')
            
        return addresses
        
    def run(self):
        # Change to the gallery directory
        os.chdir(self.gallery_dir)
        
        # Get network addresses
        ip_addresses = self.get_ip_addresses()
        
        # Print server info with beautiful formatting
        print("\n" + "="*50)
        print("✨ Gallery Server Running!")
        print("="*50)
        print(f"\n📂 Serving files from: {self.gallery_dir.absolute()}")
        print("\n🌐 Access your gallery at:")
        print("   Local:")
        print(f"   • http://localhost:{self.port}")
        print(f"   • http://127.0.0.1:{self.port}")
        if len(ip_addresses) > 1:
            print("\n   Network:")
            for addr in ip_addresses:
                if addr != '127.0.0.1':
                    print(f"   • http://{addr}:{self.port}")
        
        print("\n⚡ Server Details:")
        print(f"   • Host: {self.host}")
        print(f"   • Port: {self.port}")
        print("\n⌨️  Press Ctrl+C to stop the server")
        print("="*50 + "\n")
        
        # Open browser automatically
        webbrowser.open(f'http://localhost:{self.port}')
        
        try:
            # Start server
            self.app.run(host=self.host, port=self.port)
        except KeyboardInterrupt:
            print("\n🛑 Shutting down server...")
            print("👋 Server stopped")
            print("="*50 + "\n")

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Start a network-accessible gallery web server')
    parser.add_argument('--dir', default='./gallery_output',
                      help='Directory containing the gallery (default: ./gallery_output)')
    parser.add_argument('--port', type=int, default=8000,
                      help='Port to run the server on (default: 8000)')
    parser.add_argument('--host', default='0.0.0.0',
                      help='Host address to bind to (default: 0.0.0.0 - all interfaces)')
    
    args = parser.parse_args()
    
    # Start server
    server = GalleryServer(args.dir, args.port, args.host)
    server.run()
