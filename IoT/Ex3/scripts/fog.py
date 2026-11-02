import os, json, base64, io, time, urllib.request, ssl
from http.server import BaseHTTPRequestHandler, HTTPServer
from PIL import Image
from fc_utils import process_image, local_fraction, verify, combine_images

cloud = os.getenv("CLOUD_URL")
thres = 300000

context = ssl.create_default_context(cafile="/certs/ca.crt")            #needed for https
context.load_cert_chain("/certs/server.crt", "/certs/server.key")


class Fog(BaseHTTPRequestHandler):
    def do_POST(self):
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
            decision = "local"
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

        self.send_response(200)
        self.end_headers()
        self.wfile.write(json.dumps({"decision": decision, "original_size": len(original), "result_size": len(result), "verified": verified[0]}).encode())

server = HTTPServer(("0.0.0.0", 8000), Fog)
server_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
server_context.load_cert_chain("/certs/server.crt", "/certs/server.key")
server.socket = server_context.wrap_socket(server.socket, server_side=True)
server.serve_forever()