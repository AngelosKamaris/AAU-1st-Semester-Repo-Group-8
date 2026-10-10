
import os
import re
import json
import time
import base64
import hashlib
import argparse
import shutil
import threading

import paho.mqtt.client as mqtt

QoS = 1
TOPIC_ROOT = "ota"          #copied from server



def start_client(broker: str = "localhost"):
    "Starts the OTA client, connects to the MQTT broker, subscribes to topics and listens for messages."
    os.system("rm -r received_chunks/")
    client = connect(broker)
    subscribe_to_topics(client)
    listen_for_messages(client)
    client.loop_start()
    print(f"OTA Client connected to broker at {broker} and subscribed to topics.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("OTA Client shutting down.")
    finally:
        client.loop_stop()
        client.disconnect()




def connect(broker) -> mqtt.Client:
    "Connects to the MQTT broker and returns the client instance."
    try: client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="ota-client")
    except AttributeError:
        client =  mqtt.Client(client_id="ota-client") # changed the client id
    client.connect(broker, 1883, keepalive=60)
    return client


def subscribe_to_topics(client):
    "Subscribes the client to the manifest and chunk topics."
    client.subscribe(f"{TOPIC_ROOT}/+/manifest", qos=QoS)
    client.subscribe(f"{TOPIC_ROOT}/+/chunk/+", qos=QoS)


def listen_for_messages(client):
    "Registers the callback that receives and interprets MQTT messages."
    def handle_message(client, userdata, msg):
        topic = msg.topic
        version="0.0.0"
        try:
            payload = msg.payload.decode("utf-8")       #get payload as string
            if re.fullmatch(f"{TOPIC_ROOT}/[^/]+/manifest", topic):     #check if we received a manifest message
                manifest = json.loads(payload)
                print(f"Received manifest for firmware {manifest.get('firmware_version')}.")
                version, total_chunks, merkle_root, size = interpret_manifest(manifest)
                listen_for_chunk_messages(client, version, size, total_chunks, merkle_root, handle_message) #start listening for chunk messages
            else:
                print(f"manifest not received yet.")
        except (UnicodeDecodeError, json.JSONDecodeError, AttributeError) as exc:
            print(f"Could not process message on '{topic}': {exc}")

    client.on_message = handle_message      #listen for messages and call the handle_message function when a message is received

def interpret_manifest(manifest):
    "Interprets the manifest and prints its contents."
    firmware_version = manifest.get("firmware_version")
    total_chunks = manifest.get("chunks_num", 0)
    checksum = manifest.get("merkle_root")
    size = manifest.get("firmware_size")
    print(f"Manifest for firmware version {firmware_version}:")
    print(f"  Total chunks: {total_chunks}")
    print(f"  Checksum: {checksum}")
    print(f"  Size: {size}")
    return firmware_version, total_chunks, checksum, size


def listen_for_chunk_messages(client, version, size, total_chunks, merkle_root, manifest_callback):
    "Once manifest is received, this function listens for chunk messages and processes them."
    received_chunks = 0
    indexarr = []
    cur_size = 0

    def on_timeout():
        if received_chunks < total_chunks:
            missing = sorted(set(range(total_chunks)) - set(indexarr))
            reason = f"timeout waiting for chunks {missing} for firmware {version}"
            print(f"Timeout: {reason}.")
            shutil.rmtree(f"received_chunks/{version}", ignore_errors=True)
            if os.path.exists("firmware_reconstructed.txt"):
                os.remove("firmware_reconstructed.txt")
            with open("ota_failure.log", "a", encoding="utf-8") as log_file:
                log_file.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {reason}\n")        #if the firmware reconstruction fails, log the reason in ota_failure.log
            client.on_message = manifest_callback

    timeout_timer = threading.Timer(20, on_timeout)         #set a timeout of 20 seconds to wait for all chunks to be received, after the manifest is received. If not all chunks are received within this time, the timeout function will be called to handle the situation.
    timeout_timer.daemon = True

    def handle_message(client, userdata, msg):
        "handles incoming chunk messages, stores them, and verifies the firmware once all chunks are received."
        nonlocal received_chunks, cur_size
        topic = msg.topic
        try:
            payload = json.loads(msg.payload.decode("utf-8"))
            if re.fullmatch(f"{TOPIC_ROOT}/{version}/chunk/\\d+", topic):           #verify topic matches the expected format for chunk messages
                if payload.get("version") != version:                               #verify version in payload matches the expected version
                    with open("ota_failure.log", "a", encoding="utf-8") as log_file:
                        log_file.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - Chunk version {payload.get('version')} does not match {version}\n")
                    raise ValueError(f"chunk version {payload.get('version')} does not match {version}")
                index = payload.get("index")
                if isinstance(index, bool) or not isinstance(index, int) or index not in range(total_chunks):   #check if index is a valid integer and within the expected range
                    with open("ota_failure.log", "a", encoding="utf-8") as log_file:
                        log_file.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - Invalid chunk index: {index}\n")
                    raise ValueError(f"invalid chunk index: {index}")
                data = base64.b64decode(payload.get("data"), validate=True)
                if store_chunk(version, index, data) == 0:                      #store the chunk if it hasn't been stored already and update the received chunks count and current size
                    indexarr.append(index)
                    cur_size += len(data)
                    received_chunks += 1
                    print(f"Received chunk {index} for firmware {version}. Total received: {received_chunks}/{total_chunks}.")
                if received_chunks == total_chunks:                             #see if we received all the chunks
                    timeout_timer.cancel()
                    print(f"All chunks for firmware {version} received. Verifying Merkle root and size...")
                    if (sorted(indexarr) == list(range(total_chunks)) and cur_size == size and verify_checksum(version, total_chunks, merkle_root)):      #see that chucks have the correct indexes [0,1,2,3] and that the current size matches the expected size and that the checksum is correct
                        with open("firmware_reconstructed.txt", "wb") as output:        #create the firmware.
                            for chunk_index in range(total_chunks):
                                with open(f"received_chunks/{version}/chunk_{chunk_index}.bin", "rb") as chunk_file:
                                    output.write(chunk_file.read())
                        print(f"Firmware {version} reconstructed successfully.")
                    else:
                        print(f"Checksum verification failed or missing chunks for firmware {version} or size is wrong.")
                        print(f"Received chunks: {indexarr}, expected: {[0,1,2,3]}, current size: {cur_size}, expected size: {size}.")
                        with open("ota_failure.log", "a", encoding="utf-8") as log_file:
                            log_file.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - Checksum verification failed or missing chunks for firmware {version} or size is wrong. Received chunks: {indexarr}, expected: {[0,1,2,3]}, current size: {cur_size}, expected size: {size}.\n")
            else:
                print(f"Chunk message received for unknown version or topic: '{topic}'.")
                with open("ota_failure.log", "a", encoding="utf-8") as log_file:
                    log_file.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - Chunk message received for unknown version or topic: '{topic}'.\n")
        except (UnicodeDecodeError, json.JSONDecodeError, AttributeError, ValueError) as exc:
            print(f"Could not process message on '{topic}': {exc}")

    client.on_message = handle_message
    timeout_timer.start()


def store_chunk(version: str, index: int, data: bytes):
    "Stores the received chunk data in a file named according to the firmware version and chunk index."
    if os.path.exists(f"received_chunks/{version}/chunk_{index}.bin"):          #checks if chunk has already been stored to avoid overwriting and unnecessary processing
        print(f"Chunk {index} for firmware {version} already stored. Skipping.")
        return 1
    os.makedirs(f"received_chunks/{version}", exist_ok=True)
    with open(f"received_chunks/{version}/chunk_{index}.bin", "wb") as f:
        f.write(data)
    print(f"Stored chunk {index} for firmware {version}.")
    return 0


def verify_checksum(version: str, total_chunks: int, expected_checksum: str):
    "Verifies the Merkle root of the received chunks against the manifest."
    if total_chunks != 4:
        return False
    chunk_hashes = []
    for i in range(total_chunks):
        with open(f"received_chunks/{version}/chunk_{i}.bin", "rb") as f:       #recreates the Merkle root by hashing the chunks and combining them in pairs
            chunk_hashes.append(hashlib.sha256(f.read()).digest())
    left = hashlib.sha256(chunk_hashes[0] + chunk_hashes[1]).digest()
    right = hashlib.sha256(chunk_hashes[2] + chunk_hashes[3]).digest()
    calculated_checksum = hashlib.sha256(left + right).hexdigest()
    if calculated_checksum == expected_checksum:
        print(f"Checksum verification successful for firmware {version}.")
    else:
        print(f"Checksum verification failed for firmware {version}. Expected: {expected_checksum}, Calculated: {calculated_checksum}.")
    return calculated_checksum == expected_checksum


