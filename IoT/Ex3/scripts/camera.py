import os, time, json, base64, urllib.request, urllib.error, ssl
from pathlib import Path

images = sorted(Path("/images").glob("*"))
fog = os.getenv("FOG_URL")
context = ssl.create_default_context(cafile="/certs/ca.crt")            #needed for https

while True:
    for image in images:
        data = json.dumps({"camera": os.getenv("CAMERA_ID"), "filename": image.name, "image": base64.b64encode(image.read_bytes()).decode()}).encode()
        req = urllib.request.Request(fog + "/process", data=data, headers={"Content-Type": "application/json", "Authorization": f"Bearer {os.getenv('CAMERA_TOKEN')}"})
        # we measure the latency (the old version printed just the fog reply but not how long it took)
        start = time.perf_counter()
        try:
            reply = urllib.request.urlopen(req, context=context, timeout=180).read().decode()
        except urllib.error.HTTPError as e:          # in cases where the fog refuse the request (429 or other errors)
            reply = f"refused with status {e.code}"
        except Exception as e:                       # no answer or when we reach the timeout
            reply = f"error: {e}"
        print(f"latency_ms={round((time.perf_counter() - start) * 1000)} image={image.name} {reply}", flush=True)
        time.sleep(5)