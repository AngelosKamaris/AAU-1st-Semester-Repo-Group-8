# Mini Project 3: IoT – Fog – Cloud

A smart-city monitoring system built with Docker containers. Camera clients send
images to a nearby **fog** node, which processes part of the work locally and
offloads the rest to a **cloud** node. A separate **logger** collects structured
logs from the fog and cloud nodes. The project then measures performance, attacks
the system, and defends it.

## Architecture

| Container | Role | Networks (IP) |
|---|---|---|
| camera-1, camera-2 | cameras, Zone A | zone_a_net (1.1.2.3, 1.1.2.4) |
| camera-3 | camera, Zone B | zone_b_net (1.1.3.3) |
| fog_a | fog node, Zone A | zone_a_net (1.1.2.2), backbone_net (1.1.1.2), mgmt_net (1.1.4.2) |
| fog_b | fog node, Zone B | zone_b_net (1.1.3.2), backbone_net (1.1.1.3), mgmt_net (1.1.4.3) |
| cloud | cloud node | backbone_net (1.1.1.4), mgmt_net (1.1.4.4) |
| logger | log collector | mgmt_net (1.1.4.5) |

Networks:
- `zone_a_net` (1.1.2.0/24) and `zone_b_net` (1.1.3.0/24) are **internal**: cameras can reach only their own fog node.
- `backbone_net` (1.1.1.0/24): fog ↔ cloud processing traffic (mutual TLS).
- `mgmt_net` (1.1.4.0/24): logging traffic only.

Cameras reach their fog node over HTTPS with a per-camera API token; fog and cloud
authenticate each other with mutual TLS. A 200 ms delay is added on the fog↔cloud
link to simulate a WAN.

## Requirements

- **Docker** and **Docker Compose**. On Windows, Docker Desktop with WSL2 integration enabled; run the commands from the Ubuntu (WSL) shell.
- No other dependencies: Python and the image libraries are installed inside the containers.

## Install and start

1. Clone the repository and enter this folder:

       cd IoT/Ex3

2. Create the environment file with the camera tokens (not committed):

       cp ".env copy" .env

   `run_app.sh` does this automatically if `.env` is missing.

3. Start the whole system (builds images on first run):

       ./run_app.sh

   This runs `docker compose up --build -d` and prints the container status. Wait
   about 30 seconds, then confirm all seven containers are **Up**:

       docker compose ps

4. Follow a fog node's activity:

       docker logs -f fog_a

To stop everything:

    ./stop_app.sh

> **Before running the baseline or any experiment:** make sure `camera-2`'s
> `command` in `compose.yaml` is the normal one — `["python", "/scripts/camera.py"]`.
> The attack scripts switch `camera-2` into attacker mode themselves (via override
> files) and switch it back afterwards.

## Running the experiments

All scripts live in this folder. Make them executable once: `chmod +x *.sh`.
Results are written to `evidence/`.

| Task | Command | What it does |
|---|---|---|
| 1.3 network isolation | `./test_isolation.sh` | Shows a camera reaches its own fog node but not the cloud or the other zone. → `evidence/isolation_test.txt` |
| 1.5 WAN delay | `./measure_rtt.sh` | Prints the configured delay and measures fog↔cloud round-trip time (~400 ms). → `evidence/rtt.txt` |
| 5.1 + 5.2 DoS & mitigation | `./run_dos.sh` | Three phases — normal, attack (camera-2 floods fog_a), attack with per-client rate limiting — recording camera-1 latency for each. → `evidence/dos_*.txt` |
| 5.3 ID-switching flood | `./run_botnet.sh` | camera-2 floods fog_a while rotating valid camera IDs, with rate limiting on. Shows the limiter still blocks it (it keys on IP, not ID). → `evidence/botnet_idswitch_*.txt` |
| 5.5 MITM | `./run_mitm.sh` | An attacker takes over the cloud's address with an untrusted certificate; the fog nodes reject it. Restores the real cloud at the end. |

Each DoS/botnet phase runs for 200 seconds by default. For a quicker test, set
`WAIT`, e.g. `WAIT=120 ./run_botnet.sh`.

### How the DoS scripts control state

`run_dos.sh` and `run_botnet.sh` use small Compose override files so the attacker
and mitigation state is explicit and repeatable:

- `dos_normal.override.yaml` — camera-2 normal, rate limiting off
- `dos_attack.override.yaml` — camera-2 flooding, rate limiting off
- `dos_mitigated.override.yaml` — camera-2 flooding, rate limiting on
- `dos_idswitch.override.yaml` — camera-2 flooding with rotating IDs, rate limiting on

Rate limiting is toggled through `fog_a`'s `RATE_LIMIT` environment variable.

## Reading the results

    cat evidence/dos_normal_camera1.txt      # baseline latency
    cat evidence/dos_attack_camera1.txt      # under attack (much higher)
    cat evidence/dos_mitigated_camera1.txt   # attack with mitigation (back to normal)
    grep "rejected: rate limit" logs/system.jsonl | wc -l   # rejected requests

## Assumptions and limitations

- The whole system runs on one host, so the "WAN" is a simulated 200 ms delay and
  the networks are Docker virtual networks, not physical ones.
- Fog nodes are limited to 0.5 CPU and 256 MB to model constrained edge devices.
  Without mitigation, a flood can exhaust this and kill a fog node; with per-client
  rate limiting it stays up.
- Rate limiting is keyed on the **client IP**, so an attacker that only changes its
  camera ID is still blocked, but several distinct hosts (a true botnet) would each
  get their own allowance.
- `run_mitm.sh` requires the system to be running and restores the real cloud when
  it finishes.

## Authors

Nuria Arqués León, Ikhlasse Badidi, Martha Gaki, Angelos Kamaris, Waleed Rashed and Aicha Nadja Thorman

*MSc in Cyber Security, Aalborg University*
