import yaml
import platform
from pathlib import Path

if platform.system().lower() == "windows":
    SHARED_ROOT = Path(r"E:\JARVIS_HOME")
else:
    SHARED_ROOT = Path("/mnt/shared200/JARVIS_HOME")

SHARED_MODES = SHARED_ROOT / "identity" / "modes"

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
LOCAL_MODES = BASE_DIR / "identity" / "modes"

MODES_DIR = SHARED_MODES if SHARED_MODES.exists() else LOCAL_MODES


def load_mode(mode_name: str):

    mode_file = MODES_DIR / f"{mode_name}.yaml"

    if not mode_file.exists():
        raise FileNotFoundError(f"Mode file not found: {mode_file}")

    with open(mode_file, "r") as f:
        return yaml.safe_load(f)