import os, time, json, base64, urllib.request, ssl
from pathlib import Path

images = sorted(Path("/images").glob("*"))
fog = os.getenv("FOG_URL")
context = ssl.create_default_context(cafile="/certs/ca.crt")            #needed for https

while True:
    for image in images:
        data = json.dumps({"camera": os.getenv("CAMERA_ID"), "filename": image.name, "image": base64.b64encode(image.read_bytes()).decode()}).encode()
        req = urllib.request.Request(fog + "/process", data=data, headers={"Content-Type": "application/json", "Authorization": f"Bearer {os.getenv('CAMERA_TOKEN')}"})
        print(urllib.request.urlopen(req, context=context).read().decode(), flush=True)
        time.sleep(5)