
import argparse
import shutil
import subprocess
import sys
import time
from pathlib import Path

from ota_server import run_server
from ota_client import start_client


def run_scenario(broker_IP: str):
    print(f"OTA Serverpublishing the manifest and chunks on IP {broker_IP}. Exiting.")
    terminal = shutil.which("x-terminal-emulator")
    if terminal is None:
        raise RuntimeError("Could not find x-terminal-emulator.")

    project_dir = Path(__file__).resolve().parent
    client_code = f"from ota_client import start_client; start_client({broker_IP!r})"
    server_code = f"from ota_server import run_server; run_server({broker_IP!r})"

    subprocess.Popen([terminal, "-e", sys.executable, "-c", client_code], cwd=project_dir)
    time.sleep(2)
    subprocess.Popen([terminal, "-e", sys.executable, "-c", server_code], cwd=project_dir)


def main():
    parse = argparse.ArgumentParser(description="OTA Server for Firmware Updates")
    parse.add_argument("--broker", type=str, default="localhost", help="MQTT broker IP address")
    args = parse.parse_args()

    run_scenario(args.broker)


if __name__ == "__main__":
    main()