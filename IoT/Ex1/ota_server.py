import os
import re
import json
import time
import base64
import hashlib

import paho.mqtt.client as mqtt


NUM_CHUNKS = 4
QoS = 1
TOPIC_ROOT = "ota"

def read_firmware(file_path: str = 'firmware.txt') -> tuple[bytes, str]:
    "Reads the firmware file and returns its content as bytes."
    with open(file_path, 'rb') as f:
        firmware_data = f.read()

    firmware_text = firmware_data.decode("utf-8")
    match = re.search(r'\bversion\s+([0-9]+(?:\.[0-9]+)+)\b', firmware_text)
    if match: firmware_version = match.group(1)

    return firmware_data, firmware_version

def save_chunk(chunk_data: bytes, file_name: str) -> None:
    "Saves the given chunk data to a file."
    with open(file_name, 'wb') as f:
        f.write(chunk_data)

def split_into_chunks(firmware_data: bytes, num_chunks: int = NUM_CHUNKS) -> list[bytes]:
    "Splits the firmware data into specified number of chunks and saves them as separate files."

    if len(firmware_data) < num_chunks: raise ValueError("Firmware data is smaller than the number of chunks requested.")

    chunk_size, remainder = divmod(len(firmware_data), num_chunks)
    chunks: list[bytes] = []
    os.makedirs("chunks", exist_ok=True)
    start_index = 0
    for i in range(num_chunks):
        length = chunk_size + (1 if i < remainder else 0)  # Distribute remainder bytes among the first few chunks
        chunk_data = firmware_data[start_index:(start_index + length)]
        start_index += length

        chunks.append(chunk_data)
        save_chunk(chunk_data, os.path.join("chunks", f"chunk_{i}.txt"))

    assert b"".join(chunks) == firmware_data, "Not all firmware data was processed."
    return chunks # C0, C1, C2, C3

def build_merkle_tree(chunks: list[bytes]) -> dict[str, bytes]:
    """
    Builds the binary Merkle tree for four chunks:

                     ROOT = H(H01 || H23)                # root
                    /                    \\
          H01 = H(H0 || H1)        H23 = H(H2 || H3)     # branches
           /          \\             /          \\
         H0            H1          H2            H3      # leaves
    """
    def hash_data(data: bytes) -> bytes:
        "Hashes the given data using SHA-256 and returns the hash digest (raw binary data)."
        return hashlib.sha256(data).digest()
    
    leaves = [hash_data(c) for c in chunks] # H0, H1, H2, H3
    h01    = hash_data(leaves[0] + leaves[1])
    h23    = hash_data(leaves[2] + leaves[3])
    root   = hash_data(h01 + h23)
    return {"leaves": leaves, "h01": h01, "h23": h23, "root": root}

def create_manifest(firmware_data: bytes, firmware_version: str, chunks: list[bytes], tree: dict[str, bytes]) -> dict:
    "Creates a manifest file containing the firmware size, chunk hashes, and Merkle tree structure."
    manifest = {
        "firmware_version": firmware_version,
        "firmware_size": len(firmware_data),
        "chunks_num": len(chunks),
        "merkle_root": tree["root"].hex(),
        "chunks": [{"index": i, "filename": os.path.join("chunks", f"chunk_{i}.txt")} for i in range(len(chunks))]
    }
    with open("manifest.json", 'w') as f:
        json.dump(manifest, f, indent=4)
    return manifest

def generate_messages() -> tuple[bytes, list[bytes], str]:
    "Generates the manifest and chunk messages for OTA update."
    firmware_data, firmware_version = read_firmware(file_path="firmware.txt")

    chunks = split_into_chunks(firmware_data, NUM_CHUNKS)
    tree = build_merkle_tree(chunks)

    manifest = create_manifest(firmware_data, firmware_version, chunks, tree)
    print(f"Manifest created successfully.")
    return manifest, chunks, firmware_version

def manifest_topic(version: str) -> str:
    return f"{TOPIC_ROOT}/{version}/manifest"

def chunk_topic(version: str, chunk_index: int) -> str:
    return f"{TOPIC_ROOT}/{version}/chunk/{chunk_index}"

def chunk_payload(version: str, chunk_index: int, chunk_data: bytes) -> str:
    "Creates a payload for a specific chunk, including the version and chunk index."
    return json.dumps({"version": version, "index": chunk_index,
                       "data": base64.b64encode(chunk_data).decode("ascii")})

def connect(broker: str) -> mqtt.Client:
    "Connects to the MQTT broker and returns the client instance."
    try: client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="ota-server")
    except AttributeError:              # paho-mqtt 1.x
        client =  mqtt.Client(client_id="ota-server")
    
    client.connect(broker, 1883, keepalive=60)
    client.loop_start()
    return client

def publish(client: mqtt.Client, topic: str, payload: str) -> None:
    "Publishes a message to the specified MQTT topic with QoS level, and wait for the broker's PUBACK."
    info = client.publish(topic, payload, qos=QoS, retain=False)
    info.wait_for_publish(timeout=10) # Wait for the broker's PUBACK for delivery confirmation.
    if not info.is_published(): raise RuntimeError(f"Failed to publish message to topic '{topic}'.")
    print(f"   Published message to topic '{topic}' ({len(payload)} bytes).")


def test_scenario(broker_IP: str, scenario: str, client: mqtt.Client = None):
    "ask the user to choose a test scenario and runs the corresponding OTA update test."
    print("Choose a test scenario:")
    print("1. Normal")
    print("2. Duplicate")
    print("3. Conflict")
    print("4. Missing")
    print("5. Corrupted")
    choice = input("Enter your choice (1-5): ")
    match choice:
        case "1":  scenario = "normal"
        case "2": scenario = "duplicate"
        case "3": scenario = "conflict"
        case "4": scenario = "missing"
        case "5": scenario = "corrupted"
        case _:
            print("Invalid choice. Running normal scenario.")
            scenario = "normal"
    _, chunks, firmware_version = generate_messages()
    if client is None:
        client = connect(broker=broker_IP)

    for i, chunk in enumerate(chunks):
        if scenario == "missing" and i == len(chunks) - 1: continue
        if scenario == "corrupted" and i == 1: chunk = b"X" + chunk[1:]

        if i == 1 and scenario == "conflict":
            wrong_version = "0.9.9"
            publish(client, chunk_topic(firmware_version, i), chunk_payload(wrong_version, i, chunk))
            publish(client, chunk_topic(firmware_version, i), chunk_payload(firmware_version, i, chunk))
        else:
            publish(client, chunk_topic(firmware_version, i), chunk_payload(firmware_version, i, chunk))
        if i == 1 and scenario == "duplicate":
            publish(client, chunk_topic(firmware_version, i), chunk_payload(firmware_version, i, chunk))
        time.sleep(0.5)
    time.sleep(5)

def run_server(broker_IP: str = "localhost") -> None:
    "Runs the OTA server: generates the manifest and chunk messages, and publishes them to the MQTT broker."
    manifest, _, firmware_version = generate_messages()
    client = connect(broker=broker_IP)

    input(f"Press Enter to start publishing test ...")
    publish(client, manifest_topic(firmware_version), json.dumps(manifest))
    time.sleep(2)  # Give subscriber time to process the manifest

    # Test scenarios we can choose to run by pressing numbers for each test
    print(f"running test scenario")
    test_scenario(broker_IP, scenario="normal", client=client)
    client.loop_stop()
    client.disconnect()