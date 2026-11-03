from datetime import datetime
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from PIL import Image
import io, os, ssl
from pathlib import Path
from fc_utils import process_image, send_log

process_count = 0

class Cloud(BaseHTTPRequestHandler):
    def do_POST(self):
        start = time.perf_counter()
        data = self.rfile.read(int(self.headers["Content-Length"]))

        client_ip = self.client_address[0]

        if self.path == "/store":
            ip = self.headers["X-Client-IP"]
            filename = os.path.basename(self.headers["X-Filename"])
            folder = Path("/cloud/images") / ip
            folder.mkdir(parents=True, exist_ok=True)
            (folder / filename).write_bytes(data)
            send_log({"service": "cloud", "timestamp": datetime.now().isoformat(), "client_ip": client_ip, "request": self.path, "request_size": len(data), "processing_time": round((time.perf_counter() - start) * 1000, 2), "response_status": 200})
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Stored")
            
        elif self.path == "/process":
            global process_count
            image = Image.open(io.BytesIO(data)).convert("RGB")
            result = process_image(image)
            if process_count == 1:
                image.putpixel((0, 0), (255, 0, 0))
                output = io.BytesIO()
                image.save(output, format="PNG")
                result = output.getvalue()
                
            print(f"Cloud processed image from {client_ip}, total processed: {process_count + 1}", flush=True)
            process_count += 1
            send_log({"service": "cloud", "timestamp": datetime.now().isoformat(), "client_ip": client_ip, "request": self.path, "request_size": len(data), "processing_time": round((time.perf_counter() - start) * 1000, 2), "response_status": 200})
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