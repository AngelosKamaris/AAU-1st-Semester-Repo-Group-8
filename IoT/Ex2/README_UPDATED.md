# Mini Project 2: TPM Attestation Experiment

This project uses two TPM-enabled devices:

* **TPM-A** (signing device): a Linux laptop with its built-in hardware TPM.
* **TPM-B** (verifying device): a Raspberry Pi with a Let's Trust TPM board (Infineon SLB 9672).

TPM-A creates a TPM-backed signing key and signs the message `TPM exercise`. TPM-B verifies the signature using only the public key exported from TPM-A. The private key never leaves TPM-A.

## Requirements

* Two Linux machines, each with a TPM 2.0 (we used Ubuntu on the laptop and Raspberry Pi OS on the Pi).
* Both machines on the same network, so TPM-A can reach TPM-B over SSH.
* Python 3 on TPM-A. No extra Python packages are needed.

## 1. Install the environment

On **both** TPM-A and TPM-B:

    sudo apt update
    sudo apt install tpm2-tools

On **TPM-A** only:

    sudo apt install python3 openssh-client

On **TPM-B** only:

    sudo apt install openssh-server

The project files only need to be on TPM-A.

## 2. Start TPM-A

TPM-A uses the laptop's built-in TPM, which is available at `/dev/tpmrm0` once Linux boots. Check that it works:

    tpm2_getrandom 4 --hex

If this prints random characters, TPM-A is ready.

## 3. Start TPM-B (Raspberry Pi)

1. With the Pi powered off, connect the Let's Trust TPM board to the GPIO pins (see https://pinout.xyz/pinout/letstrust_tpm).
2. Enable the TPM driver by adding this line under `[all]` in `/boot/firmware/config.txt`:

       dtoverlay=tpm-slb9670

3. Reboot, then check that the TPM is detected:

       ls -l /dev/tpm*
       tpm2_getrandom 4 --hex

   You should see `/dev/tpm0` and `/dev/tpmrm0`, and random characters.

4. Make sure the SSH server is running (`sudo systemctl status ssh`).

**Permissions:** the user running the scripts (on TPM-A) and the SSH user (on TPM-B) must be in the `tss` group to use the TPM without `sudo`:

    sudo usermod -aG tss $USER

Log out and back in for this to take effect. Otherwise, run the script with `sudo`.

## 4. Run the experiments

All three experiments (RSA, ECC and PCR-bound signing) run from one script. On TPM-A, from the project folder (`IoT/Ex2`):

    python3 run.py

The script asks for TPM-B's SSH username and IP address (or hostname), then for the SSH password. It then runs, in order:

| Experiment | What it does | Log file |
|---|---|---|
| RSA (Task 2) | RSA-2048 key on TPM-A signs the message; TPM-B verifies it and rejects a tampered copy (`TPM exercise!`) | `evidence/rsa_sign_verify.log` |
| ECC (Task 3) | Same steps with an ECC P-256 key | `evidence/ecc_sign_verify.log` |
| PCR-bound signing (Task 4) | Key locked to PCR 23: signing works with the expected PCR value, is refused after PCR 23 changes, and TPM-B verifies the valid signature | `evidence/pcr_bound_signing.log` |

Each experiment ends with a `PASS` or `FAIL` line. The script exits with code 0 only if all three pass.

Files created on TPM-A are stored in `work/tpm_a/`. Files sent to TPM-B are stored on the Pi in `~/.tpm_ex2/work/tpm_b/`.

### Using a different TPM interface

Both TPMs are reached through `/dev/tpmrm0` by default. To change this, edit `TPM_TCTI` near the top of `tpm_utils.py`, for example:

    TPM_TCTI = {"A": "device:/dev/tpm0", "B": "device:/dev/tpm0"}

## Assumptions and limitations

* **Linux only.** The scripts need Linux with a real TPM on both machines. They were not tested on Windows or macOS.
* **PCR 23 is used for the PCR experiment** because it can be reset and does not affect the boot process. Anyone with access to TPM-A can reset it and replay the trusted measurement, so it is weaker than real boot PCRs.
* **TPM-B only checks the signature.** It cannot see the PCR policy, and it cannot confirm that the public key came from a genuine TPM. That would need a TPM certificate or quote, which this experiment does not include.
* **No freshness.** An old valid signature could be sent again, and TPM-B cannot tell when it was made.
* **PCR 23 is reset on every run**, so the script should not be run on a machine where another program relies on PCR 23.

## Authors

Nuria Arqués León, Ikhlasse Badidi, Martha Gaki, Angelos Kamaris, Waleed Rashed and Aicha Nadja Thorman

*MSc in Cyber Security, Aalborg University*
