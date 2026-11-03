import hashlib, psutil, io, os, json, urllib.request
from PIL import Image

def local_fraction(size):
    cpu = psutil.cpu_percent(interval=0.1)      #see how busy the CPU is
    print(f"CPU Usage: {cpu}%", flush=True)
    if size <= 300000:
        return 1                                #cpu was never over 20% during testing.
    elif cpu < 5:
        return 0.75
    elif cpu < 10:
        return 0.5
    else:
        return 0.25


def process_image(image):
    image = image.resize((image.width // 2, image.height))

    output = io.BytesIO()
    image.save(output, format="PNG") 

    return output.getvalue()


def verify(reference, distributed):
    reference = Image.open(io.BytesIO(reference)).convert("RGB")
    distributed = Image.open(io.BytesIO(distributed)).convert("RGB")

    reference_hash = hashlib.sha256(reference.tobytes()).hexdigest()
    distributed_hash = hashlib.sha256(distributed.tobytes()).hexdigest()

    return reference_hash == distributed_hash, reference_hash, distributed_hash

def combine_images(local, remote):
    local = Image.open(io.BytesIO(local)).convert("RGB")
    remote = Image.open(io.BytesIO(remote)).convert("RGB")
    combined = Image.new("RGB", (local.width, local.height + remote.height))
    combined.paste(local, (0, 0))
    combined.paste(remote, (0, local.height))
    output = io.BytesIO()
    combined.save(output, format="PNG")
    return output.getvalue()


def send_log(record):
    data = json.dumps(record).encode()
    request = urllib.request.Request( "http://1.1.4.5:8000/logs", data=data, headers={"Content-Type": "application/json"})
    urllib.request.urlopen(request, timeout=2).read()
