from __future__ import annotations

import re
from pathlib import Path


SUBJECT_FOLDER = {
    "programming": "Programming",
    "security": "Security",
    "religion": "Religion",
    "history": "History",
    "aviation": "Aviation",
    "academic": "Academic",
}


TYPE_FOLDER = {
    "single_document": "Documents",
    "website_archive": "Websites",
    "codebase": "Code",
    "source_collection": "Code",
    "academic_or_code_project": "Projects",
    "single_image": "Images",
    "folder_collection": "Collections",
    "single_file": "Files",
}


def safe_name(name: str) -> str:
    name = name.strip() or "Untitled"
    name = re.sub(r"[\\/:\*\?\"<>\|]+", " ", name)
    name = re.sub(r"\s+", " ", name).strip()
    return name[:160]


def destination_for(
    *,
    knowledge_root: str,
    title: str,
    subject: str | None,
    object_type: str,
    source_path: str,
) -> str:
    root = Path(knowledge_root).expanduser().resolve()

    subject_dir = SUBJECT_FOLDER.get((subject or "").lower(), "Unclassified")
    type_dir = TYPE_FOLDER.get(object_type, "Resources")

    src = Path(source_path)
    name = safe_name(src.name if src.is_file() else title)

    return str(root / subject_dir / type_dir / name)
