from pathlib import Path
import subprocess
import sys


PROFILE_MAP = {
    "ubuntu": "linux.txt",
    "kali": "linux.txt",
    "linux": "linux.txt",
    "windows": "windows.txt",
    "macos": "macos.txt",
}


class DependencyBootstrap:

    def prepare(self, environment: str):

        print("Checking Python dependencies...")

        profile = PROFILE_MAP.get(environment)

        if profile is None:
            raise RuntimeError(
                f"No dependency profile defined for '{environment}'"
            )

        requirements = Path("requirements") / profile

        if not requirements.exists():
            raise FileNotFoundError(
                f"Missing dependency profile: {requirements}"
            )

        print(f"Dependency profile : {profile}")

        #
        # Always make sure pip is current
        #

        subprocess.run(
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                "--upgrade",
                "pip",
            ],
            check=True,
        )

        #
        # Install the profile
        #

        subprocess.run(
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                "-r",
                str(requirements),
            ],
            check=True,
        )

        print("✓ Dependencies verified")
