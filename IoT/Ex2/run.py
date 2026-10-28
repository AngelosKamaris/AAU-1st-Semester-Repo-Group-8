import os, sys, time
from pathlib import Path

from tpm_utils import connect_tpm_b, disconnect_tpm_b, workdir
from sign_verify import create_primary_key, sign_message, verify_signature, get_log


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
    connect_tpm_b()
    all_ok = True

    for kt, alg in ALGORITHMS.items():
        t0 = time.perf_counter()
        context = create_primary_key(kt, alg)
        t_create = time.perf_counter() - t0

        t0 = time.perf_counter()
        message_file = sign_message(context, kt, alg, message=MESSAGE)
        t_sign = time.perf_counter() - t0

        t0 = time.perf_counter()
        ok = verify_signature(message_file, kt, alg, label="original message")
        t_verify = time.perf_counter() - t0

        get_log(kt).say(f"\nTIMING {kt.upper()}: key creation={t_create:.3f} s, "
                f"sign={t_sign:.3f} s, verify={t_verify:.3f} s")

        tampered_file = os.path.join(workdir("A"), f"{kt}_message_tampered.txt")
        Path(tampered_file).write_text(TAMPERED)
        bad = verify_signature(tampered_file, kt, alg, label=f"TAMPERED message {TAMPERED!r}")

        passed = ok and not bad
        get_log(kt).say(f"\n{kt.upper()} RESULT: original verified={ok}, "
                        f"tampered rejected={not bad} -> {'PASS' if passed else 'FAIL'}")
        
        all_ok &= passed # if any test fails, the final exit code will be 1

    disconnect_tpm_b()
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()