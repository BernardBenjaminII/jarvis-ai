from __future__ import annotations

import json
import re
import sqlite3
from pathlib import Path
from html.parser import HTMLParser


class TitleParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.in_title = False
        self.title_parts: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() == "title":
            self.in_title = True

    def handle_endtag(self, tag):
        if tag.lower() == "title":
            self.in_title = False

    def handle_data(self, data):
        if self.in_title:
            self.title_parts.append(data.strip())

    @property
    def title(self) -> str | None:
        text = " ".join(part for part in self.title_parts if part).strip()
        return text or None


def guess_subject_from_path(path: str) -> str | None:
    p = path.lower()

    rules = [
        ("programming", ["programming", "code", "python", "c++", "cpp", "java", "cmake"]),
        ("history", ["history", "war", "diary", "afghanistan", "afg"]),
        ("religion", ["deen", "quran", "islam", "hadith"]),
        ("aviation", ["aviation", "blackhawk", "uh-60", "faa"]),
        ("security", ["hacking", "cyber", "security", "pentest"]),
        ("academic", ["school", "course", "assignment", "project"]),
    ]

    for subject, needles in rules:
        if any(needle in p for needle in needles):
            return subject

    return None


def inspect_website(row: sqlite3.Row, conn: sqlite3.Connection) -> dict:
    object_path = row["object_path"]

    members = conn.execute(
        """
        SELECT file_path
        FROM knowledge_object_files
        WHERE object_uuid=?
        """,
        (row["object_uuid"],),
    ).fetchall()

    html_count = 0
    image_count = 0
    css_count = 0
    js_count = 0
    title = None

    for member in members:
        path = Path(member["file_path"])
        ext = path.suffix.lower()

        if ext in {".html", ".htm"}:
            html_count += 1
        elif ext in {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".ico"}:
            image_count += 1
        elif ext == ".css":
            css_count += 1
        elif ext == ".js":
            js_count += 1

    primary = row["primary_file_path"]
    if primary and Path(primary).exists():
        try:
            raw = Path(primary).read_text(encoding="utf-8", errors="ignore")[:200_000]
            parser = TitleParser()
            parser.feed(raw)
            title = parser.title
        except Exception:
            title = None

    title = title or row["object_name"]

    return {
        "title": title,
        "description": f"Website archive containing {html_count} HTML pages.",
        "language": None,
        "primary_subject": guess_subject_from_path(object_path),
        "keywords": ",".join(filter(None, [guess_subject_from_path(object_path), "website_archive"])),
        "metadata": {
            "html_pages": html_count,
            "images": image_count,
            "css_files": css_count,
            "js_files": js_count,
            "primary_file": primary,
        },
    }


def inspect_document(row: sqlite3.Row, conn: sqlite3.Connection) -> dict:
    path = Path(row["primary_file_path"] or row["object_path"])
    title = path.stem.replace("_", " ").replace("-", " ").strip()

    return {
        "title": title,
        "description": f"Standalone document: {path.name}",
        "language": None,
        "primary_subject": guess_subject_from_path(str(path)),
        "keywords": ",".join(filter(None, [guess_subject_from_path(str(path)), path.suffix.lower().lstrip(".")])),
        "metadata": {
            "extension": path.suffix.lower(),
            "filename": path.name,
            "size_bytes": row["total_size_bytes"],
            "primary_file": str(path),
        },
    }


def inspect_codebase(row: sqlite3.Row, conn: sqlite3.Connection) -> dict:
    members = conn.execute(
        """
        SELECT file_path
        FROM knowledge_object_files
        WHERE object_uuid=?
        """,
        (row["object_uuid"],),
    ).fetchall()

    language_counts: dict[str, int] = {}

    ext_map = {
        ".py": "python",
        ".c": "c",
        ".cpp": "cpp",
        ".h": "c/cpp header",
        ".hpp": "cpp header",
        ".java": "java",
        ".js": "javascript",
        ".ts": "typescript",
        ".rs": "rust",
        ".go": "go",
        ".sh": "shell",
        ".sql": "sql",
    }

    for member in members:
        ext = Path(member["file_path"]).suffix.lower()
        lang = ext_map.get(ext)
        if lang:
            language_counts[lang] = language_counts.get(lang, 0) + 1

    primary_language = max(language_counts, key=language_counts.get) if language_counts else None

    return {
        "title": row["object_name"],
        "description": f"Code resource with primary language: {primary_language or 'unknown'}.",
        "language": primary_language,
        "primary_subject": "programming",
        "keywords": ",".join(["codebase", primary_language or "unknown"]),
        "metadata": {
            "language_counts": language_counts,
            "file_count": row["file_count"],
        },
    }


def inspect_generic(row: sqlite3.Row, conn: sqlite3.Connection) -> dict:
    return {
        "title": row["object_name"],
        "description": f"{row['object_type']} resource.",
        "language": None,
        "primary_subject": guess_subject_from_path(row["object_path"]),
        "keywords": row["object_type"],
        "metadata": {
            "file_count": row["file_count"],
            "size_bytes": row["total_size_bytes"],
        },
    }


def inspect_resource(row: sqlite3.Row, conn: sqlite3.Connection) -> dict:
    object_type = row["object_type"]

    if object_type == "website_archive":
        return inspect_website(row, conn)

    if object_type in {"single_document", "epub_extracted_book"}:
        return inspect_document(row, conn)

    if object_type in {"codebase", "python_project", "node_project", "source_collection"}:
        return inspect_codebase(row, conn)

    return inspect_generic(row, conn)


def to_metadata_json(data: dict) -> str:
    return json.dumps(data.get("metadata", {}), ensure_ascii=False, sort_keys=True)
