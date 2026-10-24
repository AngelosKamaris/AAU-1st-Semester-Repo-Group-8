import os, sys
from pathlib import Path

from tpms import start_tpms, stop_tpms
from sign_verify import create_primary_key, sign_message, verify_signature, get_log
from tpm_utils import workdir

MESSAGE = "TPM exercise"
TAMPERED = "TPM exercise!"

ALGORITHMS = {
    "rsa": {
        "key_template": "rsa2048:rsapss-sha256:null", # RSA-2048, PSS, SHA-256
        "sign_scheme": "rsapss",
        "load_alg": "rsa",                              
    },
    "ecc": {
        "key_template": "ecc256:ecdsa-sha256", # NIST P-256, ECDSA, SHA-256
        "sign_scheme": "ecdsa",
        "load_alg": "ecc",
    },
}


def main():
    start_tpms()
    all_ok = True

    for kt, alg in ALGORITHMS.items():
        context = create_primary_key(kt, alg)
        message_file = sign_message(context, kt, alg, message=MESSAGE)

        ok = verify_signature(message_file, kt, alg, label="original message")

        tampered_file = os.path.join(workdir("A"), f"{kt}_message_tampered.txt")
        Path(tampered_file).write_text(TAMPERED)
        bad = verify_signature(tampered_file, kt, alg, label=f"TAMPERED message {TAMPERED!r}")

        passed = ok and not bad
        get_log(kt).say(f"\n{kt.upper()} RESULT: original verified={ok}, "
                        f"tampered rejected={not bad} -> {'PASS' if passed else 'FAIL'}")
        
        all_ok &= passed # if any test fails, the final exit code will be 1

    stop_tpms()
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()