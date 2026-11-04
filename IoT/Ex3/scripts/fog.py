import time
from datetime import datetime
import os, json, base64, io, urllib.request, ssl
from http.server import BaseHTTPRequestHandler, HTTPServer
from PIL import Image
from fc_utils import process_image, local_fraction, verify, combine_images, send_log
import collections

cloud = os.getenv("CLOUD_URL")
thres = 300000
# 5.2 per-client rate limiting
RATE_LIMIT = os.getenv("RATE_LIMIT", "off") == "on"     # switch, set in compose.yaml
MAX_REQUESTS = 5                                         # max requests per client...
WINDOW = 10                                              # ...in this many seconds
history = collections.defaultdict(collections.deque)    # client IP -> times of its recent requests




context = ssl.create_default_context(cafile="/certs/ca.crt")            #needed for https
context.load_cert_chain("/certs/server.crt", "/certs/server.key")

def rate_limited(ip):
    now = time.time()
    times = history[ip]
    while times and now - times[0] > WINDOW:     # forget requests older than 30 s
        times.popleft()
    if len(times) >= MAX_REQUESTS:               # already 5 recent requests: refuse
        return True
    times.append(now)                            # otherwise remember this one and accept
    return False

class Fog(BaseHTTPRequestHandler):
    def do_POST(self):
        start_time = time.perf_counter()
        # 5.2 rate limiting: checked before any other work
        client_ip = self.client_address[0]
        if RATE_LIMIT and rate_limited(client_ip):
            self.rfile.read(int(self.headers["Content-Length"]))     # read and discard the image
            send_log({"service": "fog", "timestamp": datetime.now().isoformat(), "client_ip": client_ip, "decision": "rejected: rate limit", "response_status": 429})
            self.send_error(429, "Too Many Requests")
            return       
        data = json.loads(self.rfile.read(int(self.headers["Content-Length"])))

        camera = data.get("camera")
        key = os.getenv(camera) if camera else None

        if not key or self.headers.get("Authorization") != f"Bearer {key}":
            self.log_message("Rejected unauthenticated request from %s", self.client_address[0])
            self.send_error(401, "Unauthorized")
            return
        original = base64.b64decode(data["image"])
        image = Image.open(io.BytesIO(original)).convert("RGB")
        fraction = local_fraction(len(original))

        if fraction >= 1:
            result = process_image(image)
            decision = "processed locally"
        else:
            split = int(image.height * fraction)
            local = process_image(image.crop((0, 0, image.width, split)))
            remote_image = image.crop((0, split, image.width, image.height))
            buffer = io.BytesIO()
            remote_image.save(buffer, format="PNG")
            request = urllib.request.Request(cloud + "/process", data=buffer.getvalue(), headers={"Content-Type": "application/octet-stream"})
            remote = urllib.request.urlopen(request, context=context).read()
            result = combine_images(local, remote)
            decision = "offloaded with a fraction of " + str(fraction)

        # Verify against processing the complete image locally
        reference = process_image(image)
        verified = verify(result, reference)
        if verified[0]:
            request = urllib.request.Request(cloud + "/store", data=result, headers={"Content-Type": "application/octet-stream", "X-Client-IP": self.client_address[0], "X-Filename": data["filename"]})
            urllib.request.urlopen(request, context=context).read()

        end_time = time.perf_counter()
        log_record = { "service": "fog", "timestamp": datetime.now().isoformat(), "client_ip": self.client_address[0], "camera": camera, "decision": decision, "original_size": len(original), "result_size": len(result), "verified": verified[0], "reference_hash": verified[1], "result_hash": verified[2], "processing_time": end_time - start_time}
        send_log(log_record)
        self.send_response(200)
        self.end_headers()
        self.wfile.write(json.dumps({"decision": decision, "original_size": len(original), "result_size": len(result), "verified": verified[0]}).encode())

server = HTTPServer(("0.0.0.0", 8000), Fog)
server_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
server_context.load_cert_chain("/certs/server.crt", "/certs/server.key")
server.socket = server_context.wrap_socket(server.socket, server_side=True)
server.serve_forever()