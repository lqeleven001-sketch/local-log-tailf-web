import http.server
import socketserver

PORT = 18082

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        print(f"接收到请求: {self.path}")
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b"<html><body><h1>Test Server</h1><p>Hello World!</p></body></html>")

print(f"测试服务器启动在 http://localhost:{PORT}")
with socketserver.TCPServer(("", PORT), MyHTTPRequestHandler) as httpd:
    httpd.serve_forever()
