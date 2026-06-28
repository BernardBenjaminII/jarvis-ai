import subprocess
from pathlib import Path


OUTPUT_DIR = Path("/mnt/jarvis_ai/recon/scans/subdomains")


def run_subfinder(domain):

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    output_file = OUTPUT_DIR / f"{domain}.txt"

    cmd = [
        "subfinder",
        "-d",
        domain,
        "-silent"
    ]

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True
    )

    output_file.write_text(result.stdout)

    return {
        "domain": domain,
        "output_file": str(output_file),
        "results": result.stdout.splitlines()
    }
