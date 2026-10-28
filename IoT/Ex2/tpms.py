from tpm_utils import connect_tpm_b, disconnect_tpm_b


def start_tpms():
    """Connect to TPM-B; TPM-A is the local hardware TPM."""
    connect_tpm_b()

 
def stop_tpms():
    """Close the SSH connection to TPM-B."""
    disconnect_tpm_b()