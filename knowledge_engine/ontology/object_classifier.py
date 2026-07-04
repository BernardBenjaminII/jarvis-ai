from __future__ import annotations

from pathlib import Path

from knowledge_engine.ontology import object_types as T


SOURCE_EXTENSIONS = {
    ".py", ".pyw", ".java", ".c", ".h", ".cpp", ".hpp", ".cc", ".cxx",
    ".cs", ".rs", ".go", ".js", ".jsx", ".ts", ".tsx", ".php", ".rb",
    ".swift", ".kt", ".scala", ".sh", ".ps1", ".sql", ".asm",
}

SCRIPT_EXTENSIONS = {".sh", ".ps1", ".bat", ".cmd"}

CONFIG_EXTENSIONS = {
    ".yaml", ".yml", ".toml", ".ini", ".cfg", ".conf", ".json",
}

DOCUMENT_EXTENSIONS = {
    ".pdf", ".epub", ".docx", ".md", ".txt", ".rtf",
}

DATA_EXTENSIONS = {
    ".csv", ".json", ".xml", ".sqlite", ".db",
}

IMAGE_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff", ".svg",
}

ARCHIVE_EXTENSIONS = {
    ".zip", ".tar", ".gz", ".tgz", ".bz2", ".xz", ".7z", ".rar",
}

SPECIAL_FILENAMES = {
    "Makefile": T.CONFIGURATION,
    "CMakeLists.txt": T.CONFIGURATION,
    "Dockerfile": T.CONFIGURATION,
    "README.md": T.TECHNICAL_DOCUMENT,
}


def classify_object(object_path: str, current_type: str | None = None) -> tuple[str, float, str]:
    path = Path(object_path)
    name = path.name
    lower = object_path.lower()
    ext = path.suffix.lower()

    if name in SPECIAL_FILENAMES:
        return SPECIAL_FILENAMES[name], 0.95, f"special filename: {name}"

    if any(marker in lower for marker in ["/.git", "pyproject.toml", "package.json"]):
        return T.SOFTWARE_PROJECT, 0.90, "software project marker"

    if "project" in lower:
        return T.ACADEMIC_PROJECT, 0.80, "path suggests project"

    if "course" in lower or "ocw" in lower:
        return T.COURSE, 0.80, "path suggests course"

    if current_type in {"website_archive", "web_or_html_collection"}:
        return T.WEBSITE_ARCHIVE, 0.90, f"existing object type: {current_type}"

    if current_type == "academic_or_code_project":
        return T.ACADEMIC_PROJECT, 0.80, "existing object type suggests project"

    if ext in SCRIPT_EXTENSIONS:
        return T.SCRIPT, 0.90, f"script extension: {ext}"

    if ext in SOURCE_EXTENSIONS:
        return T.SOURCE_FILE, 0.95, f"source extension: {ext}"

    if ext in CONFIG_EXTENSIONS:
        return T.CONFIGURATION, 0.85, f"configuration extension: {ext}"

    if ext in IMAGE_EXTENSIONS:
        return T.IMAGE, 0.90, f"image extension: {ext}"

    if ext in DATA_EXTENSIONS:
        return T.DATASET, 0.80, f"data extension: {ext}"

    if ext in ARCHIVE_EXTENSIONS:
        return T.ARCHIVE, 0.85, f"archive extension: {ext}"

    if ext in DOCUMENT_EXTENSIONS:
        if any(term in lower for term in ["manual", "faa", "tm ", "technical manual", "handbook"]):
            return T.REFERENCE_MANUAL, 0.85, "manual-like document"
        if any(term in lower for term in ["paper", "research", "journal", "proceedings"]):
            return T.RESEARCH_PAPER, 0.80, "research-like document"
        if ext in {".md", ".txt"}:
            return T.NOTE, 0.75, f"note-like extension: {ext}"
        return T.BOOK, 0.75, f"book-like document extension: {ext}"

    if path.is_dir():
        if any(term in lower for term in ["src", "source", "code", "github"]):
            return T.SOFTWARE_PROJECT, 0.75, "directory suggests software project"
        return T.FOLDER_COLLECTION, 0.60, "directory fallback"

    return T.UNKNOWN, 0.25, "no canonical rule matched"
