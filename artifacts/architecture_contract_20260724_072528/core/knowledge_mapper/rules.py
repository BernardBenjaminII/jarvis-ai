from pathlib import Path
import yaml

RULE_FILE = Path("knowledge/mapping/folder_rules.yaml")

def load_rules():
    with open(RULE_FILE, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)["rules"]
