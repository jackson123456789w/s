from http.server import BaseHTTPRequestHandler, HTTPServer

class RedirectHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if "zsbitovska.cz" in self.headers.get('Host', ''):
            self.send_response(302)
            self.send_header('Location', 'https://www.google.com')
            self.end_headers()
        else:
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"You're not visiting zsbitovska.com")

server = HTTPServer(('0.0.0.0', 80), RedirectHandler)
print("Server running on port 80...")
server.serve_forever()
