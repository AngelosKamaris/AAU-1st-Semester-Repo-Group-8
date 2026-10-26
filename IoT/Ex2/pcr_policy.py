"""Task 4: PCR-bound signing key.

TPM-A creates an ECC signing key that can only be used when PCR 23
has a predefined expected value. TPM-B verifies the signature using
only the exported public key.
"""

from pathlib import Path

from tpm_utils import run, Log, workdir, flush, transfer

PCR_SELECTION = "sha256:23"       # PCR 23, SHA-256 bank (resettable, safe to use)
KEY_TEMPLATE = "ecc256:ecdsa-sha256"
TRUSTED = "trusted-app-v1"        # stands in for trusted software
UNTRUSTED = "untrusted-app"       # stands in for untrusted software

log = Log("pcr_bound_signing")


def flush_all(tpm: str):
    """Free object AND session slots (sessions are left behind if a command fails)."""
    flush(tpm)
    run(["tpm2_flushcontext", "-l"], tpm, None, check=False)  # loaded sessions
    run(["tpm2_flushcontext", "-s"], tpm, None, check=False)  # saved sessions


def set_expected_pcr_state():
    """1. Reset PCR 23 and record the trusted file into it."""

    d = workdir("A")
    log.banner("1. TPM-A: set the predefined (expected) PCR state")

    measurement = d / "measurement.txt"
    measurement.write_text(TRUSTED + "\n")

    run(["tpm2_pcrreset", "23"], "A", log)
    run(["tpm2_pcrevent", "23", measurement], "A", log)
    run(["tpm2_pcrread", PCR_SELECTION], "A", log)


def create_pcr_policy() -> Path:
    """2a. Trial session: turn the rule 'PCR 23 = expected value' into a policy digest."""

    d = workdir("A")
    log.banner("2a. TPM-A: create the PCR policy")

    trial = d / "trial.ctx"
    policy = d / "pcr.policy"

    flush_all("A")
    run(["tpm2_startauthsession", "-S", trial], "A", log)
    run(["tpm2_policypcr", "-S", trial, "-l", PCR_SELECTION, "-L", policy], "A", log)
    run(["tpm2_flushcontext", trial], "A", log)

    log.say("policy digest: " + policy.read_bytes().hex())
    return policy


def create_pcr_key(policy: Path) -> Path:
    """2b. Create an ECC signing key with the PCR policy attached; export the public key."""

    d = workdir("A")
    log.banner("2b. TPM-A: create a signing key restricted by the PCR policy")

    primary = d / "pcr_primary.ctx"
    pub, priv, ctx = d / "pcr_key.pub", d / "pcr_key.priv", d / "pcr_key.ctx"

    flush_all("A")
    run(["tpm2_createprimary", "-C", "o", "-g", "sha256", "-G", "ecc", "-c", primary], "A", log)

    # No 'userwithauth': the key can ONLY be used by satisfying the PCR policy
    flush("A")
    run(["tpm2_create", "-C", primary, "-g", "sha256", "-G", KEY_TEMPLATE,
         "-a", "fixedtpm|fixedparent|sensitivedataorigin|sign",
         "-L", policy, "-u", pub, "-r", priv], "A", log)

    flush("A")
    run(["tpm2_load", "-C", primary, "-u", pub, "-r", priv, "-c", ctx], "A", log)

    # Show the key's attributes and authorization policy (evidence)
    flush("A")
    run(["tpm2_readpublic", "-c", ctx], "A", log)

    log.banner("2c. TPM-A: export ONLY the public key")
    flush("A")
    run(["tpm2_readpublic", "-c", ctx, "-o", d / "pcr_pub.pem", "-f", "pem"], "A", log)

    return ctx


def sign_with_pcr_policy(ctx: Path, sig_name: str, label: str) -> bool:
    """3/4. Open a policy session, let the TPM check PCR 23, then try to sign."""

    d = workdir("A")
    log.banner(f"TPM-A: sign 'TPM exercise' ({label})")

    message = d / "pcr_message.txt"
    message.write_text("TPM exercise")   # exact message, no newline
    session = d / "session.ctx"

    flush_all("A")
    run(["tpm2_startauthsession", "--policy-session", "-S", session], "A", log)
    run(["tpm2_policypcr", "-S", session, "-l", PCR_SELECTION], "A", log)
    p = run(["tpm2_sign", "-c", ctx, "-g", "sha256", "-s", "ecdsa",
             "-p", f"session:{session}", "-o", d / sig_name, message],
            "A", log, check=False)   # a failure is expected when the PCR has changed
    flush_all("A")

    ok = p.returncode == 0
    log.say(f">>> Signing ({label}): {'ALLOWED' if ok else 'REFUSED'}")
    return ok


def change_pcr_state():
    """Record an untrusted file into PCR 23 so it no longer matches."""

    d = workdir("A")
    log.banner("TPM-A: change PCR 23 (untrusted software measured)")

    untrusted = d / "untrusted.txt"
    untrusted.write_text(UNTRUSTED + "\n")

    run(["tpm2_pcrevent", "23", untrusted], "A", log)
    run(["tpm2_pcrread", PCR_SELECTION], "A", log)


def verify_on_tpm_b(sig_name: str) -> bool:
    """5. TPM-B: verify using only the public key, the message and the signature."""

    a = workdir("A")
    log.banner("5. TPM-B: verify the signature made under the valid PCR state")

    b_pem = transfer(a / "pcr_pub.pem", "B", log)
    b_sig = transfer(a / sig_name, "B", log)
    b_msg = transfer(a / "pcr_message.txt", "B", log)
    ctx = workdir("B") / "pcr_pub.ctx"

    flush("B")
    run(["tpm2_loadexternal", "-C", "n", "-G", "ecc", "-u", b_pem, "-c", ctx], "B", log)
    p = run(["tpm2_verifysignature", "-c", ctx, "-g", "sha256",
             "-s", b_sig, "-m", b_msg], "B", log, check=False)
    flush("B")

    ok = p.returncode == 0
    log.say(f">>> TPM-B verification: {'VERIFIED' if ok else 'REJECTED'}")
    return ok
