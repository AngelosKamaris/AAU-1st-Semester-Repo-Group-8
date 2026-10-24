import os
from pathlib import Path

from tpm_utils import run, Log, workdir, flush, transfer

_logs = {}

def get_log(key_type: str) -> Log:
    """One log per algorithm: ECC and RSA"""

    if key_type not in _logs:
        _logs[key_type] = Log(f"{key_type}_sign_verify")
    return _logs[key_type]


def create_primary_key(key_type: str, alg: dict) -> str:
    """TPM-A: create a primary key + TPM-backed signing key; return the key context path."""

    log = get_log(key_type)
    d = workdir("A")    

    # Primary key (the parent type matches the child: rsa or ecc)
    log.banner(f"TPM-A: create {key_type.upper()} primary + signing key")
    flush("A")
    primary = os.path.join(d, f"{key_type}_primary.ctx")
    run(["tpm2_createprimary", "-C", "o", "-g", "sha256", "-G", key_type, "-c", primary], "A", log)

    # Signing key: RSA-2048/RSASSA-PSS or ECC P-256/ECDSA
    flush("A")
    pub, priv, ctx = os.path.join(d, f"{key_type}_key.pub"), os.path.join(d, f"{key_type}_key.priv"), os.path.join(d, f"{key_type}_key.ctx")
    # fixedtpm|fixedparent: cannot be duplicated/exported
    # sign: signing only
    run(["tpm2_create", "-C", primary, "-g", "sha256", "-G", alg["key_template"],
         "-a", "fixedtpm|fixedparent|sensitivedataorigin|userwithauth|sign", 
         "-u", pub, "-r", priv], "A", log)

    # Load the key into the TPM
    flush("A")
    run(["tpm2_load", "-C", primary, "-u", pub, "-r", priv, "-c", ctx], "A", log)

    # Export only the public material required for verification
    log.banner("TPM-A: export ONLY the public key")
    pem = os.path.join(d, f"{key_type}_pub.pem")
    run(["tpm2_readpublic", "-c", ctx, "-o", pem, "-f", "pem"], "A", log)

    return ctx


def sign_message(context: str, key_type: str, alg: dict, message="TPM exercise") -> str:
    """TPM-A: sign the message; return the message file path (on host A)."""

    log = get_log(key_type)
    d = workdir("A")
    message_file = os.path.join(d, f"{key_type}_message.txt")
    Path(message_file).write_text(message)

    log.banner(f"TPM-A: sign {message!r}")
    flush("A")
    sig = os.path.join(d, f"{key_type}_signature.sig")
    run(["tpm2_sign", "-c", context, "-g", "sha256", "-s", alg["sign_scheme"], "-o", sig, message_file], "A", log)

    return message_file


def verify_signature(message_file: str, key_type: str, alg: dict, label="original message") -> bool:
    """TPM-B: verify using only the exported public key. Returns True if verified."""

    log = get_log(key_type)
    a = workdir("A")

    log.banner(f"TPM-B: verify {label}")
    # Transfer the public key, signature, and message to TPM-B
    b_pem = transfer(os.path.join(a, f"{key_type}_pub.pem"), "B", log)
    b_sig = transfer(os.path.join(a, f"{key_type}_signature.sig"), "B", log)
    b_msg = transfer(message_file, "B", log)
    ctx = os.path.join(workdir("B"), f"{key_type}_pub.ctx")

    # Load the public key into TPM-B and verify the signature
    flush("B")
    run(["tpm2_loadexternal", "-C", "n", "-G", alg["load_alg"], "-u", b_pem, "-c", ctx],"B", log)
    p = run(["tpm2_verifysignature", "-c", ctx, "-g", "sha256", "-s", b_sig, "-m", b_msg], "B", log, check=False) # a failure is expected
    flush("B")

    ok = p.returncode == 0 # 0 = verified, 1 = rejected
    log.say(f">>> {key_type.upper()} {label}: {'VERIFIED' if ok else 'REJECTED'}")
    return ok