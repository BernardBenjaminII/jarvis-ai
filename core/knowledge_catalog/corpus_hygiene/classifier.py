from pathlib import Path

KNOWN_METADATA = {".DS_Store", "Thumbs.db", "desktop.ini"}

def classify_filesystem_artifact(path: str):
    name = Path(path).name
    if name.startswith("._"):
        return "EXCLUDED_APPLEDOUBLE", "macOS AppleDouble/resource-fork sidecar."
    if name in KNOWN_METADATA:
        return "EXCLUDED_FILESYSTEM_METADATA", f"Known filesystem metadata: {name}"
    return None, None
