# Mini Project 1: Investigating OTA Firmware Integrity Using MQTT and Merkle Trees

A simulated over-the-air (OTA) firmware update system over MQTT. A server splits a firmware image into chunks, builds a Merkle tree over them, and publishes a manifest and the chunks. A client receives them, verifies integrity against the Merkle root, and reconstructs the firmware.

The firmware here is a simulated text file (`firmware.txt`).

## How it works

1. **Server** (`ota_server.py`)
   - Reads `firmware.txt` and extracts the version from the text.
   - Splits the data into 4 chunks (saved in `chunks/`).
   - Builds a binary Merkle tree (SHA-256) over the chunks:
     ```
                  ROOT = H(H01 || H23)
                 /                    \
          H01 = H(H0 || H1)      H23 = H(H2 || H3)
           /        \              /        \
         H0         H1           H2         H3
     ```
   - Writes `manifest.json` and publishes the manifest and chunks with QoS 1.

2. **Client** (`ota_client.py`)
   - Subscribes to topics: `ota/+/manifest` and `ota/+/chunk/+`.
   - On receiving a manifest, waits up to 20 seconds for all chunks.
   - Validates each chunk's version and index, ignores duplicates, and stores chunks in `received_chunks/<version>/`.
   - Once all chunks arrive, checks the chunk indexes, total size and Merkle root. On success it writes `firmware_reconstructed.txt`.
   - Failures (version mismatch, bad index, timeout, checksum mismatch) are logged to `ota_failure.log`.

## MQTT topics

| Topic | Content |
|---|---|
| `ota/<version>/manifest` | JSON: version, size, chunk count, Merkle root, chunk list |
| `ota/<version>/chunk/<index>` | JSON: version, index, base64-encoded chunk data |

## Project structure

```
firmware.txt      Simulated firmware image
ota_server.py     Publishes manifest and chunks
ota_client.py     Receives, verifies and reconstructs firmware
run.py            Launches client and server in separate terminals
requirements.txt  Python dependencies
```

## Requirements

- Python 3.10 or newer (the server uses `match` statements)
- An MQTT broker on port 1883, such as [Mosquitto](https://mosquitto.org/)
- Python package: `paho-mqtt` (see `requirements.txt`)

## Setup

### 1. Check your Python version

```bash
python --version
```

It must be 3.10 or newer. 

### 2. Create a virtual environment

From the project folder:

```bash
python -m venv venv
```

### 3. Activate it

Linux / macOS:

```bash
source venv/bin/activate
```

Windows (Command Prompt):

```bat
venv\Scripts\activate.bat
```

Your prompt should now start with `(venv)`.

### 4. Install the dependencies

```bash
pip install -r requirements.txt
```

### 5. Install and start an MQTT broker

On Debian/Ubuntu:

```bash
sudo apt install mosquitto
sudo systemctl start mosquitto
```

On Windows, install Mosquitto from mosquitto.org and start its service.

To check that the broker is listening on port 1883, run `mosquitto -v` (if you started it manually) or check that the service is running.

### 6. Run the project

See [Usage](#usage) below. Remember to activate the virtual environment (step 3) in every new terminal you open.


## Usage

### Option 1: run.py

```bash
python run.py --broker <MQTT broker IP address>
```

This opens the client and the server in two terminal windows. It uses `x-terminal-emulator`, so it works on Debian/Ubuntu-style Linux.

### Option 2: run manually (any OS)

Open two terminals in the project folder and start the client first:

```bash
python -c "from ota_client import start_client; start_client()"
```

```bash
python -c "from ota_server import run_server; run_server()"
```

Pass a broker address as an argument if the broker isn't on `localhost`, for example `start_client("192.168.1.10")` and `run_server("192.168.1.10")`.

## Test scenarios

After the server publishes the manifest, press Enter and choose a scenario among the 5 possible indexes:

|  | Scenario | Behavior | Expected client result |
|---|---|---|---|
| 1 | Normal | All 4 chunks sent in order | Firmware reconstructed |
| 2 | Duplicate | Chunk 1 sent twice | Duplicate skipped, firmware reconstructed |
| 3 | Conflict | Chunk 1 sent first with a wrong version, then correctly | Wrong-version chunk rejected and logged, firmware reconstructed |
| 4 | Missing | Last chunk never sent | Timeout after 20 s, partial data deleted, failure logged |
| 5 | Corrupted | Chunk 1 altered | Merkle root mismatch, failure logged |

## Output files

- `manifest.json` and `chunks/` (server)
- `received_chunks/<version>/` (client, cleared on startup)
- `firmware_reconstructed.txt` (client, only on successful verification)
- `ota_failure.log` (client, appended on failures)

## Limitations

- The client's Merkle verification supports exactly 4 chunks, matching `NUM_CHUNKS = 4` on the server.
- The firmware file must be in the working directory.
- The connection uses plain MQTT without TLS or authentication, and the Merkle root itself is not signed, so this is a simulation and not a secure update mechanism.

## Authors
Nuria Arqués León, Ikhlasse Badidi, Martha Gaki, Angelos Kamaris, Waleed Rashed, and Aicha Nadja Thorman 

*MSc in Cyber Security, Aalborg University*
