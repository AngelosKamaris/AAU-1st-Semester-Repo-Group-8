import atexit
import os
import shlex
import subprocess
from pathlib import Path

ROOT = Path().cwd()
WORK = ROOT / "work"
EVID = ROOT / "evidence"
SSH_TARGET = None
SSH_CONTROL = Path.home() / ".ssh" / "tpm-ex2-%C"


def tcti(tpm: str) -> str:
    """TCTI for a real TPM, overridable per host."""

    return os.environ.get(f"TPM_{tpm}_TCTI", "device:/dev/tpmrm0")


def connect_tpm_b():
    """Connect to TPM-B over SSH; OpenSSH handles host-key and password prompts."""
    global SSH_TARGET
    username = input("TPM-B SSH username: ").strip()
    host = input("TPM-B IP address: ").strip()
    if (not username or not host or username.startswith("-") or host.startswith("-")
            or any(c.isspace() for c in username + host)):
        raise ValueError("A valid TPM-B username and IP address are required.")

    SSH_TARGET = f"{username}@{host}"
    SSH_CONTROL.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    result = subprocess.run(
        ["ssh", "-MNf", "-o", "ControlMaster=yes", "-o", "ControlPersist=600",
         "-o", f"ControlPath={SSH_CONTROL}", SSH_TARGET]
    )
    if result.returncode:
        SSH_TARGET = None
        raise RuntimeError("Could not establish SSH connection to TPM-B.")
    atexit.register(disconnect_tpm_b)

    result = subprocess.run(
        ["ssh", "-S", str(SSH_CONTROL), SSH_TARGET,
         "cd \"$HOME\" && mkdir -p .tpm_ex2/work/tpm_b"],
        capture_output=True, text=True
    )
    if result.returncode:
        raise RuntimeError("Could not prepare TPM-B workspace:\n" + result.stderr.strip())


def disconnect_tpm_b():
    """Close the persistent SSH connection, if one was opened."""
    global SSH_TARGET
    if SSH_TARGET:
        subprocess.run(
            ["ssh", "-S", str(SSH_CONTROL), "-O", "exit", SSH_TARGET],
            check=False
        )
        SSH_TARGET = None


def workdir(tpm: str) -> Path:
    """Private folder per TPM host: work/tpm_a, work/tpm_b."""
    if tpm == "B":
        return Path(".tpm_ex2/work/tpm_b")
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
    # Specify on the log file the TPM performing the command
    if log:
        who = "TPM-" + tpm if tpm else "host"
        log.say(f"[{who}] $ " + prettify(" ".join(cmd)))

    if tpm == "B":
        if not SSH_TARGET:
            raise RuntimeError("Connect to TPM-B before running TPM-B commands.")
        remote_cmd = (
            f"cd \"$HOME\" && TPM2TOOLS_TCTI={shlex.quote(tcti(tpm))} "
            + shlex.join(cmd)
        )
        result = subprocess.run(
            ["ssh", "-S", str(SSH_CONTROL), "-o", "BatchMode=yes",
             SSH_TARGET, remote_cmd],
            capture_output=True, text=True
        )
    else:
        env = os.environ.copy()
        if tpm:
            env["TPM2TOOLS_TCTI"] = tcti(tpm)
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
    """Copy a file to the other host."""

    src = Path(src) 
    dst = Path(os.path.join(workdir(dst_tpm), src.name))
    if dst_tpm == "B":
        if not SSH_TARGET:
            raise RuntimeError("Connect to TPM-B before transferring files.")
        result = subprocess.run(
            ["scp", "-o", f"ControlPath={SSH_CONTROL}", "-o", "BatchMode=yes",
             str(src), f"{SSH_TARGET}:{dst}"],
            capture_output=True, text=True
        )
        if result.returncode:
            raise RuntimeError("Could not transfer file to TPM-B:\n" + result.stderr.strip())
    else:
        dst.write_bytes(src.read_bytes())
    log.say(f"[transfer] {src.name} -> TPM-{dst_tpm} host ({src.stat().st_size} bytes)")
    return dst