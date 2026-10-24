# Mini Project 2: TPM Attestation Experiment

The main objective of this project is to create an experiment involving two TPM-enabled devices:
* TPM-A: the signing or attesting device.
* TPM-B: the verifying device.

While TPM-A must create a TPM-backed signing key and use it to sign the following message, TPM-B must verify the signed data using the public verification material exported from TPM-A. The private signing key must not be exported from TPM-A in ordinary software-key form.

## Supported platforms

| Platform | Status |
|---|---|
| Linux (Ubuntu/Debian, Raspberry Pi OS) | Supported |
| Windows 10/11 via **WSL2** (Ubuntu) | Supported (simulators only) |
| Native Windows / macOS | Not supported: `swtpm` and `tpm2-tools` are not available |

Although the Python code uses only standard libraries and is OS-independent, the limitation comes from the TPM tools it calls.

## Setup

The experiment needs **system packages (apt)**. 

1. System dependencies (required, pip cannot install these):
       
       sudo apt update
       sudo apt install swtpm swtpm-tools tpm2-tools openssl python3 python3-venv
       sudo apt install libtss2-tcti-swtpm0t64 || sudo apt install libtss2-tcti-swtpm0


2. Python: version 3.9+ is recommended. No third-party packages are needed, so there is no `pip install -r requirements.txt` step.   

3. Verify the install:

       swtpm --version && tpm2_getcap -v

On Windows, first open PowerShell or Command Prompt as administrator, and install WSL2 with Ubuntu (`wsl --install`), then run everything inside the Ubuntu shell. 

## Authors
Nuria Arqués León, Ikhlasse Badidi, Martha Gaki, Angelos Kamaris, Waleed Rashed, and Aicha Nadja Thorman 

*MSc in Cyber Security, Aalborg University*