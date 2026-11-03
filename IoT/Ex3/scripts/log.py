import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from datetime import datetime

class Logger(BaseHTTPRequestHandler):
    def do_POST(self):
        data = { "service_ip": self.client_address[0], **json.loads(self.rfile.read(int(self.headers["Content-Length"])))}

        if data.get("verified") is False:
            print(f"ALERT: Image verification failed on {data['service']}", flush=True)
            alert = {"service_ip": self.client_address[0], "service": "logger", "timestamp": datetime.now().isoformat(), "type": "alert", "message": f"Image verification failed on {data['service']}"}
            with open("/logs/system.jsonl", "a") as file:
                file.write(json.dumps(alert) + "\n")

        with open("/logs/system.jsonl", "a") as file:
            file.write(json.dumps(data) + "\n")


        self.send_response(200)
        self.end_headers()

server = HTTPServer(("0.0.0.0", 8000), Logger)
server.serve_forever()