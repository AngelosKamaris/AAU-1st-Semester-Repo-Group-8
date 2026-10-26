"""Task 4: run the PCR-bound signing experiment from start to finish."""

import sys

from tpms import start_tpms, stop_tpms
from pcr_policy import (log, set_expected_pcr_state, create_pcr_policy, create_pcr_key,
                        sign_with_pcr_policy, change_pcr_state, verify_on_tpm_b)


def main():
    start_tpms()

    set_expected_pcr_state()                                                   # 1
    policy = create_pcr_policy()                                               # 2
    ctx = create_pcr_key(policy)                                               # 2
    signed_ok = sign_with_pcr_policy(ctx, "pcr_signature.sig", "PCR matches")  # 3
    change_pcr_state()                                                         # 4
    signed_bad = sign_with_pcr_policy(ctx, "pcr_signature_bad.sig", "PCR changed")  # 4
    verified = verify_on_tpm_b("pcr_signature.sig")                            # 5

    passed = signed_ok and not signed_bad and verified
    log.say(f"\nPCR RESULT: signing allowed with expected PCR={signed_ok}, "
            f"signing refused after PCR change={not signed_bad}, "
            f"TPM-B verified={verified} -> {'PASS' if passed else 'FAIL'}")

    stop_tpms()
    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
