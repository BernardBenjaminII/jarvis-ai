from __future__ import annotations
import json
from pathlib import Path
from typing import Any
class CoverageInventoryError(RuntimeError): pass
def load_json(path:Path)->dict[str,Any]:
    if not path.is_file(): raise CoverageInventoryError(f"Required JSON artifact is missing: {path}")
    try: value=json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc: raise CoverageInventoryError(f"Invalid JSON artifact: {path}") from exc
    if not isinstance(value,dict): raise CoverageInventoryError(f"JSON artifact must contain an object: {path}")
    return value
def load_repository_audit(audit_directory:Path):
    return (load_json(audit_directory/'constitutional_repository_audit.json'),load_json(audit_directory/'constitutional_article_usage.json'),load_json(audit_directory/'constitutional_repository_inventory.json'))
