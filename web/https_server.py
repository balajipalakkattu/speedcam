import http.server
import ssl

server_address = ('0.0.0.0', 5500)
httpd = http.server.HTTPServer(server_address, http.server.SimpleHTTPRequestHandler)

httpd.socket = ssl.wrap_socket(
    httpd.socket,
    keyfile="C:/DEV/AI-samples/certs/local.key",
    certfile="C:/DEV/AI-samples/certs/local.crt",
    server_side=True
)

print("Serving HTTPS on port 5500...")
httpd.serve_forever()