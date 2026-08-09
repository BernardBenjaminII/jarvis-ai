from __future__ import annotations
from pathlib import Path
from typing import Any

SUPPORTED_DEFAULT = {
    ".pdf", ".md", ".txt", ".html", ".htm", ".docx", ".epub"
}
CONTAINER_EXTENSIONS = {
    ".zim", ".zip", ".tar", ".gz", ".7z", ".rar", ".iso"
}

def resolve_path(row: dict[str, Any], knowledge_root: Path) -> Path | None:
    for key in (
        "file_path", "document_path", "path", "source_path",
        "local_path", "relative_path",
    ):
        value = row.get(key)
        if not value:
            continue
        candidate = Path(str(value)).expanduser()
        if not candidate.is_absolute():
            candidate = knowledge_root / candidate
        return candidate
    return None

def classify_record(
    row: dict[str, Any],
    *,
    knowledge_root: Path,
    supported_extensions: set[str],
    runtime_paths: set[str],
    duplicate_paths: set[str],
    failed_paths: set[str],
    deferred_states: set[str],
) -> dict[str, Any]:
    path = resolve_path(row, knowledge_root)
    raw_path = "" if path is None else str(path)
    ext = "" if path is None else path.suffix.casefold()
    state = str(
        row.get("lifecycle_state")
        or row.get("status")
        or row.get("state")
        or ""
    ).casefold()

    if raw_path in runtime_paths:
        disposition = "ALREADY_MATERIALIZED"
        reason = "Path exists in runtime_documents."
    elif path is None:
        disposition = "UNKNOWN"
        reason = "No usable path column was found."
    elif raw_path in failed_paths:
        disposition = "FAILED_MATERIALIZATION"
        reason = "Failure history references this path."
    elif state in deferred_states:
        disposition = "DEFERRED_BY_POLICY"
        reason = f"Lifecycle state is {state!r}."
    elif ext in CONTAINER_EXTENSIONS:
        disposition = "CONTAINER_OR_ARCHIVE"
        reason = f"Container/archive extension {ext}."
    elif ext and ext not in supported_extensions:
        disposition = "UNSUPPORTED_MEDIA_TYPE"
        reason = f"Extension {ext} not in supported set."
    elif not path.exists():
        disposition = "MISSING_SOURCE_FILE"
        reason = "Resolved source path does not exist."
    elif not path.is_file():
        disposition = "CONTAINER_OR_ARCHIVE"
        reason = "Resolved path is not a regular file."
    elif raw_path in duplicate_paths:
        disposition = "DUPLICATE_SOURCE"
        reason = "Duplicate registry references this path."
    else:
        try:
            size = path.stat().st_size
        except OSError:
            disposition = "UNREADABLE_SOURCE"
            reason = "Source stat failed."
        else:
            if size == 0:
                disposition = "EMPTY_SOURCE"
                reason = "Source file is empty."
            else:
                disposition = "ELIGIBLE_NOT_SELECTED"
                reason = "Readable supported source absent from runtime_documents."

    return {
        "path": raw_path,
        "extension": ext,
        "state": state,
        "disposition": disposition,
        "reason": reason,
        "source_row": row,
    }
