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

The experiment needs **system packages (apt)** on both TPM VMs. TPM-B must also run an SSH server.

1. System dependencies (required, pip cannot install these):
       
       sudo apt update
       sudo apt install tpm2-tools openssl python3 python3-venv
       sudo apt install openssh-client
       # On TPM-B:
       sudo apt install openssh-server


2. Python: version 3.9+ is recommended. No third-party packages are needed, so there is no `pip install -r requirements.txt` step.   

3. Verify the install:

       tpm2_getcap -v

On Windows, first open PowerShell or Command Prompt as administrator, and install WSL2 with Ubuntu (`wsl --install`), then run everything inside the Ubuntu shell. 

## Running with two TPM VMs

Run.py and all its accompaning files need only be on TPM-A, which should be able to connect via ssh to TPM-B. From `IoT/Ex2` on TPM-A, run `python3 run.py` or `python3 run_pcr.py`. The script asks for TPM-B's SSH username and IP (name can be used if it has been setup); OpenSSH prompts for its password. TPM commands run on their respective hosts.

The default TCTI for both hosts is `device:/dev/tpmrm0`. To use another TPM interface, edit `TPM_TCTI` near the top of `tpm_utils.py`:

       TPM_TCTI = {"A": "device:/dev/tpm0", "B": "device:/dev/tpm0"}

Use TCTI values supported by each host's installed plugin.

## Authors
Nuria Arqués León, Ikhlasse Badidi, Martha Gaki, Angelos Kamaris, Waleed Rashed, and Aicha Nadja Thorman 

*MSc in Cyber Security, Aalborg University*