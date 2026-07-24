from __future__ import annotations

import json
from pathlib import Path


def load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def extract_course_metadata(extracted_root: Path) -> dict:
    metadata = {
        "metadata_files": [],
        "title": None,
        "course_id": None,
        "department": None,
    }

    for name in ["data.json", "content_map.json"]:
        p = extracted_root / name
        if p.exists():
            data = load_json(p)
            if data is not None:
                metadata["metadata_files"].append(name)

                if isinstance(data, dict):
                    metadata["title"] = metadata["title"] or data.get("title")
                    metadata["course_id"] = metadata["course_id"] or data.get("course_id")
                    metadata["department"] = metadata["department"] or data.get("department")

    return metadata


def write_metadata(out_path: Path, metadata: dict) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")
