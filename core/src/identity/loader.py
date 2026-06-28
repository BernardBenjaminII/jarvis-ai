import yaml
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
MODES_DIR = BASE_DIR / "identity" / "modes"


def load_mode(mode_name: str):

    mode_file = MODES_DIR / f"{mode_name}.yaml"

    if not mode_file.exists():
        raise FileNotFoundError(f"Mode file not found: {mode_file}")

    with open(mode_file, "r") as f:
        return yaml.safe_load(f)
