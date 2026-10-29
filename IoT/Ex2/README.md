# Mini Project 2: TPM Attestation Experiment

The main objective of this project is to create an experiment involving two TPM-enabled devices:
* TPM-A: the signing or attesting device.
* TPM-B: the verifying device.

While TPM-A must create a TPM-backed signing key and use it to sign the following message, TPM-B must verify the signed data using the public verification material exported from TPM-A. The private signing key must not be exported from TPM-A in ordinary software-key form.

## Supported platforms

| Platform | Status |
|---|---|
| Linux (Ubuntu/Debian, Raspberry Pi OS) | Supported |
| Windows 10/11 via **WSL2** (Ubuntu) | Not supported for hardware-TPM setup (supported for emulation)|
| Native Windows / macOS | Not supported for hardware-TPM setup (supported for emulation) |

The experiment requires Linux and `tpm2-tools`. Each host can use any TPM supported by its installed TPM2-TSS TCTI plugin.

## Setup

TPM-A and TPM-B both need `tpm2-tools` and access to their configured TPM. TPM-A also needs Python and an SSH client; TPM-B needs an SSH server. The project files only need to be cloned on TPM-A.

1. Install on both TPM-A and TPM-B:
       
       sudo apt update
       sudo apt install tpm2-tools

2. Install on TPM-A:

       sudo apt install openssl python3 python3-venv openssh-client

3. Install on TPM-B:

       sudo apt install openssh-server

Python 3.9+ is recommended on TPM-A. No third-party Python packages are needed, so there is no `pip install -r requirements.txt` step.

4. Verify TPM access on both hosts:

       tpm2_getcap -v

On Windows, first open PowerShell or Command Prompt as administrator, and install WSL2 with Ubuntu (`wsl --install`), then run everything inside the Ubuntu shell. 

## Running with two TPM VMs

The project files only need to be on TPM-A, which connects to TPM-B over SSH. TPM-B must have `tpm2-tools` installed because verification commands run there. From `IoT/Ex2` on TPM-A, run `python3 run.py` to run the RSA, ECC, and PCR-bound signing experiments. The script asks for TPM-B's SSH username and IP (a hostname also works if configured); OpenSSH prompts for its password. TPM commands run on their respective hosts.

The default TCTI for both hosts is `device:/dev/tpmrm0`. To use another TPM interface, edit `TPM_TCTI` near the top of `tpm_utils.py`:

       TPM_TCTI = {"A": "device:/dev/tpm0", "B": "device:/dev/tpm0"}

Use TCTI values supported by each host's installed plugin.

## Authors
Nuria Arqués León, Ikhlasse Badidi, Martha Gaki, Angelos Kamaris, Waleed Rashed, and Aicha Nadja Thorman 

*MSc in Cyber Security, Aalborg University*