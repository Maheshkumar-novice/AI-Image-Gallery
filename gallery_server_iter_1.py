from http.server import HTTPServer, SimpleHTTPRequestHandler
import webbrowser
import argparse
import os
from pathlib import Path

class GalleryServer:
    def __init__(self, gallery_dir="./gallery_output", port=8000):
        self.gallery_dir = Path(gallery_dir)
        self.port = port
        
    def run(self):
        # Change to the gallery directory
        os.chdir(self.gallery_dir)
        
        # Create server
        server_address = ('', self.port)
        httpd = HTTPServer(server_address, SimpleHTTPRequestHandler)
        
        # Print server info
        print(f"\n✨ Gallery server running!")
        print(f"📂 Serving files from: {self.gallery_dir.absolute()}")
        print(f"🌐 View your gallery at: http://localhost:{self.port}")
        print("⌨️  Press Ctrl+C to stop the server\n")
        
        # Open browser automatically
        webbrowser.open(f'http://localhost:{self.port}')
        
        try:
            # Start server
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n🛑 Shutting down server...")
            httpd.server_close()
            print("👋 Server stopped")

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Start a simple gallery web server')
    parser.add_argument('--dir', default='./gallery_output',
                      help='Directory containing the gallery (default: ./gallery_output)')
    parser.add_argument('--port', type=int, default=8000,
                      help='Port to run the server on (default: 8000)')
    
    args = parser.parse_args()
    
    # Start server
    server = GalleryServer(args.dir, args.port)
    server.run()
