import os
import time
import signal
import shutil

from tpm_utils import run, Log, PORTS, WORK


def start_tpms():
    """Start two independent TPM simulators."""
    log = Log("tpm_instances")
    log.banner("Starting two independent TPM simulators")

    run(["pkill", "swtpm"], None, log, check=False) # kill old simulations running in the background
    time.sleep(1)

    for name, port in PORTS.items():
        state = WORK / f"swtpm_state_{name}"
        if state.exists(): shutil.rmtree(state)
        state.mkdir(parents=True, exist_ok=True)

        cmd = ["swtpm", "socket", "--tpm2", "--tpmstate", f"dir={state}",
               "--server", f"type=tcp,port={port}", "--ctrl", f"type=tcp,port={port + 1}",
               "--flags", "not-need-init,startup-clear", "--daemon",
               "--pid", f"file={state}/swtpm.pid"]
        run(cmd, None, log)

    time.sleep(1)

 
def stop_tpms():
    """Stop both simulators."""

    for n in PORTS:
        pid = WORK / f"swtpm_state_{n}" / "swtpm.pid"
        if pid.exists():
            try:
                os.kill(int(pid.read_text().strip()), signal.SIGTERM)
                print(f"stopped TPM-{n}")
            except ProcessLookupError: print(f"TPM-{n} not running")