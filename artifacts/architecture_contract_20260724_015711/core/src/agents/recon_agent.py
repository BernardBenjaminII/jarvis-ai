from ..services.recon.subfinder_service import run_subfinder
from ..services.recon.network_scan_service import scan_local_network


def handle_recon(question):

    q = question.lower().strip()

    #
    # Local network commands
    #

    if q in [
        "scan network",
        "map network",
        "discover hosts",
        "host discovery",
    ]:
        return scan_local_network()

    #
    # Domain recon
    #

    words = question.split()

    domain = None

    for word in words:

        if "." in word:
            domain = word.strip()

    if not domain:
        return (
            "Specify a domain "
            "(example: recon tesla.com) "
            "or use 'scan network'."
        )

    results = run_subfinder(domain)

    return (
        f"Recon completed for {domain}\n\n"
        f"Subdomains Found: {len(results['results'])}\n"
        f"Output File: {results['output_file']}"
    )
