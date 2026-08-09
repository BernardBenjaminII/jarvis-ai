from __future__ import annotations
import shutil
import subprocess

def tesseract_info() -> dict:
    exe = shutil.which("tesseract")
    if not exe:
        return {"available": False, "path": None, "version": None, "languages": []}

    try:
        version = subprocess.run(
            [exe, "--version"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        ).stdout.splitlines()[0]
    except Exception:
        version = None

    languages = []
    try:
        result = subprocess.run(
            [exe, "--list-langs"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        languages = [
            line.strip()
            for line in result.stdout.splitlines()[1:]
            if line.strip()
        ]
    except Exception:
        pass

    return {
        "available": True,
        "path": exe,
        "version": version,
        "languages": languages,
    }
