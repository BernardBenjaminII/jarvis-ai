from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class DocumentInspection:
    path: Path
    declared_extension: str
    detected_type: str
    magic: str
    readable: bool
    reason: str


def inspect_document(path: Path) -> DocumentInspection:
    path = Path(path)
    ext = path.suffix.lower().lstrip(".")

    try:
        with path.open("rb") as f:
            header = f.read(32)
    except Exception as exc:
        return DocumentInspection(path, ext, "unreadable", "", False, str(exc))

    magic = header[:8].decode("latin-1", errors="replace")

    if header.startswith(b"%PDF"):
        return DocumentInspection(path, ext, "pdf", magic, True, "valid_pdf_header")

    if header.lstrip().startswith((b"<!DOC", b"<!doc", b"<html", b"<HTML")):
        return DocumentInspection(path, ext, "html", magic, True, "html_content")

    if header.startswith(b"PK"):
        if ext == "epub":
            return DocumentInspection(path, ext, "epub", magic, False, "epub_reader_not_enabled")
        return DocumentInspection(path, ext, "zip", magic, False, "zip_like_content")

    if header.startswith((b"GIF87a", b"GIF89a")):
        return DocumentInspection(path, ext, "image", magic, False, "gif_image")

    if header.startswith(b"\x89PNG"):
        return DocumentInspection(path, ext, "image", magic, False, "png_image")

    if header.startswith(b"\xff\xd8\xff"):
        return DocumentInspection(path, ext, "image", magic, False, "jpeg_image")

    if ext in {"txt", "md", "csv", "json", "xml", "html", "htm"}:
        return DocumentInspection(path, ext, ext, magic, True, "text_like_extension")

    if ext == "zim":
        return DocumentInspection(path, ext, "zim", magic, False, "zim_reader_not_enabled")

    return DocumentInspection(path, ext or "none", "unknown", magic, False, "unknown_file_type")
