import os
import subprocess
from pathlib import Path

ROOT = Path().cwd()
WORK = ROOT / "work"
EVID = ROOT / "evidence"
PORTS = {"A": 2321, "B": 2323}


def tcti(tpm: str) -> str:
    """TCTI for a TPM: 
        For a real TPM, the TCTI is device:/dev/tpmrm0
        For a simulator, it is swtpm:host=<ip>,port=<port>"""

    # TODO!: CHECK WHAT HAPPENS WITH THE RASPBERRY PI
    return os.environ.get(f"TPM_{tpm}_TCTI", f"swtpm:host=127.0.0.1,port={PORTS[tpm]}")


def workdir(tpm: str) -> Path:
    """Private folder per TPM host: work/tpm_a, work/tpm_b."""
    d = WORK / f"tpm_{tpm.lower()}"
    d.mkdir(parents=True, exist_ok=True)
    return d

def prettify(text: str) -> str:
    """Hide machine-specific paths in log output."""
    return text.replace(str(WORK), ".").replace(str(ROOT), ".")

class Log:
    """Prints text to the screen and saves it to evidence/<name>.log"""

    def __init__(self, name: str):
        EVID.mkdir(parents=True, exist_ok=True)
        self.file = os.path.join(EVID, f"{name}.log")
        Path(self.file).write_text("")  # empty file

    # Append to the log file 
    def say(self, text: str = ""):
        print(text)
        with open(self.file, "a") as f: f.write(text + "\n")

    # Title of an entry in the log file
    def banner(self, text: str):
        self.say("\n=== " + text + " ===") 


def run(cmd: list, tpm: str = None, log: Log = None, check: bool = True) -> subprocess.CompletedProcess:
    """Run a command, log it, and raise if it fails (unless check=False)."""

    cmd = [str(c) for c in cmd]
    env = os.environ.copy() # which TPM to talk to ("A" or "B")

    if tpm: env["TPM2TOOLS_TCTI"] = tcti(tpm)

    # Specify on the log file the TPM performing the command
    if log:
        who = "TPM-" + tpm if tpm else "host"
        log.say(f"[{who}] $ " + prettify(" ".join(cmd)))

    # Run the command (Linux CLI) and capture its output
    result = subprocess.run(cmd, env=env, capture_output=True, text=True)
    output = (result.stdout + result.stderr).strip()

    if log:
        if output: log.say(output)
        log.say("exit code: " + str(result.returncode))

    if check and result.returncode != 0: 
        raise RuntimeError("Command failed: " + prettify(" ".join(cmd)) + "\n" + output)
    return result


def flush(tpm: str):
    """Free transient object slots (a simulator only has 3 available)."""
    run(["tpm2_flushcontext", "-t"], tpm=tpm, log=None, check=False)


def transfer(src: str, dst_tpm: str, log: Log) -> Path:
    """Simulate moving a file to the other host."""

    src = Path(src) 
    dst = Path(os.path.join(workdir(dst_tpm), src.name))
    dst.write_bytes(src.read_bytes())
    log.say(f"[transfer] {src.name} -> TPM-{dst_tpm} host ({dst.stat().st_size} bytes)")
    return dst