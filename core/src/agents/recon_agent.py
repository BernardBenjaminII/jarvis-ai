from ..services.recon.subfinder_service import run_subfinder


def handle_recon(question):

    words = question.split()

    domain = None

    for word in words:

        if "." in word:
            domain = word.strip()

    if not domain:
        return "No domain detected."

    results = run_subfinder(domain)

    return (
        f"Recon completed for {domain}\n\n"
        f"Subdomains Found: {len(results['results'])}\n"
        f"Output File: {results['output_file']}"
    )
