"""JARVIS R1.2A: bounded, read-only catalog inventory."""
from __future__ import annotations

import re
import sqlite3
from pathlib import Path


_PATTERNS = (
    r"what (?:documents?|files|materials) are (?:available|indexed|stored)(?: in (?:the |your )?(?:knowledge )?catalog)?",
    r"what (?:documents?|files) (?:do you have|are in (?:the |your )?(?:knowledge )?catalog)",
    r"(?:list|show)(?: me)? (?:the |your )?(?:available |indexed )?(?:documents?|files)(?: in (?:the |your )?(?:knowledge )?catalog)?",
    r"how many (?:documents?|files) (?:do you have|are (?:in|indexed in) (?:the |your )?(?:knowledge )?catalog)",
    r"what (?:knowledge )?collections are available",
    r"(?:list|show)(?: me)? (?:the |your )?(?:knowledge )?collections",
)

def inventory_request(question: str) -> bool:
    text = " ".join(str(question or "").casefold().split())
    text = text.rstrip(" ?.!")

    return any(
        re.fullmatch(pattern, text)
        for pattern in _PATTERNS
    )


def inspect_inventory(database_path, limit: int = 12) -> dict:
    path = Path(database_path)
    result = {
        "status": "unavailable",
        "counts": {},
        "collections": [],
        "sample_titles": [],
    }

    if not path.is_file():
        result["error"] = "Catalog database is missing."
        return result

    limit = max(1, min(int(limit), 25))

    try:
        uri = path.resolve().as_uri() + "?mode=ro"

        with sqlite3.connect(uri, uri=True, timeout=5) as db:
            db.execute("PRAGMA query_only=ON")

            tables = {
                row[0]
                for row in db.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                )
            }

            for table in (
                "runtime_documents",
                "runtime_chunks",
                "catalog_documents",
                "collections",
                "document_subjects",
            ):
                if table in tables:
                    result["counts"][table] = db.execute(
                        f'SELECT COUNT(*) FROM "{table}"'
                    ).fetchone()[0]

            if "runtime_documents" in tables:
                result["sample_titles"] = [
                    row[0]
                    for row in db.execute(
                        'SELECT DISTINCT title FROM runtime_documents '
                        'WHERE title IS NOT NULL AND title != "" '
                        'ORDER BY title LIMIT ?',
                        (limit,),
                    )
                ]

            if "collections" in tables:
                columns = {
                    row[1]
                    for row in db.execute(
                        'PRAGMA table_info("collections")'
                    )
                }

                name_column = next(
                    (c for c in ("name", "title", "label")
                     if c in columns),
                    None,
                )

                if name_column:
                    result["collections"] = [
                        row[0]
                        for row in db.execute(
                            f'SELECT DISTINCT "{name_column}" '
                            'FROM "collections" '
                            f'WHERE "{name_column}" IS NOT NULL '
                            f'ORDER BY "{name_column}" LIMIT ?',
                            (limit,),
                        )
                    ]

            result["status"] = "available"

    except (sqlite3.Error, OSError, ValueError) as exc:
        result["status"] = "error"
        result["error"] = str(exc)

    return result


def render_inventory(result: dict) -> str:
    if result["status"] != "available":
        return "JARVIS could not read the catalog inventory."

    counts = result["counts"]

    lines = [
        "JARVIS Knowledge Catalog Inventory",
        "",
        "Indexed database records:",
    ]

    for key, label in (
        ("runtime_documents", "Runtime documents"),
        ("runtime_chunks", "Runtime chunks"),
        ("catalog_documents", "Catalog documents"),
        ("collections", "Collections"),
        ("document_subjects", "Subject records"),
    ):
        if key in counts:
            lines.append(f"- {label}: {counts[key]:,}")

    if result["collections"]:
        lines.extend([
            "",
            "Sample collection names:",
            *[f"- {name}" for name in result["collections"]],
        ])

    if result["sample_titles"]:
        lines.extend([
            "",
            "Sample indexed document titles:",
            *[f"- {title}" for title in result["sample_titles"]],
        ])

    lines.extend([
        "",
        "These counts represent database records, not necessarily "
        "unique files or qualified evidence. Lists are bounded samples.",
    ])

    return "\n".join(lines)
