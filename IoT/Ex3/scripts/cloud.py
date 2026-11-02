from http.server import BaseHTTPRequestHandler, HTTPServer
from PIL import Image
import io, os, ssl
from pathlib import Path
from fc_utils import process_image

class Cloud(BaseHTTPRequestHandler):
    def do_POST(self):
        data = self.rfile.read(int(self.headers["Content-Length"]))

        if self.path == "/store":
            ip = self.headers["X-Client-IP"]
            filename = os.path.basename(self.headers["X-Filename"])
            folder = Path("/cloud/images") / ip
            folder.mkdir(parents=True, exist_ok=True)
            (folder / filename).write_bytes(data)
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Stored")
            
        elif self.path == "/process":
            image = Image.open(io.BytesIO(data)).convert("RGB")
            result = process_image(image)
            self.send_response(200)
            self.end_headers()
            self.wfile.write(result)

server = HTTPServer(("0.0.0.0", 8000), Cloud)

context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
context.load_cert_chain("/certs/server.crt", "/certs/server.key")
context.load_verify_locations("/certs/ca.crt")
context.verify_mode = ssl.CERT_REQUIRED

server.socket = context.wrap_socket(server.socket, server_side=True)
server.serve_forever()