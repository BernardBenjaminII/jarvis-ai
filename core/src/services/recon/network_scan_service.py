import subprocess


def scan_local_network():

    try:
        result = subprocess.run(
            ["ip", "route"],
            capture_output=True,
            text=True,
            timeout=10
        )

        route = result.stdout

        network = None

        for line in route.splitlines():

            parts = line.split()

            if not parts:
                continue

            candidate = parts[0]

            if candidate == "default":
                continue

            if "/" in candidate:
                network = candidate
                break

        if not network:
            return "Unable to determine local network."

        scan = subprocess.run(
            ["nmap", "-sn", network],
            capture_output=True,
            text=True,
            timeout=120
        )

        return scan.stdout

    except Exception as e:
        return f"Network scan failed: {e}"
