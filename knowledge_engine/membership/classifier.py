from __future__ import annotations

from pathlib import Path


SOURCE_EXTENSIONS = {
    ".py", ".pyw", ".java", ".c", ".h", ".cpp", ".hpp", ".cc", ".cxx",
    ".cs", ".rs", ".go", ".js", ".jsx", ".ts", ".tsx", ".php", ".rb",
    ".swift", ".kt", ".scala", ".sh", ".ps1", ".sql", ".asm",
}

DOCUMENT_EXTENSIONS = {
    ".pdf", ".epub", ".docx", ".md", ".txt", ".rtf",
}

IMAGE_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff", ".svg",
}

DATA_EXTENSIONS = {
    ".csv", ".json", ".xml", ".yaml", ".yml", ".toml", ".ini",
}

ARCHIVE_EXTENSIONS = {
    ".zip", ".tar", ".gz", ".tgz", ".bz2", ".xz", ".7z", ".rar",
}


def classify_member(file_path: str, role: str | None = None) -> tuple[str, str, str, int, str]:
    path = Path(file_path)
    name = path.name
    lower_name = name.lower()
    lower_path = file_path.lower()
    ext = path.suffix.lower()

    if name in {"README.md", "README", "readme.txt"}:
        return "documentation", "primary", "document_processor", 95, "readme documentation"

    if name in {"Makefile", "CMakeLists.txt", "Dockerfile"}:
        return "build_file", "supporting", "source_code_processor", 80, f"build file: {name}"

    if lower_name.startswith("license"):
        return "license", "supporting", "document_processor", 60, "license file"

    if lower_name.startswith("requirements") or lower_name in {"package.json", "pyproject.toml"}:
        return "dependency_manifest", "supporting", "source_code_processor", 85, "dependency manifest"

    if ext in SOURCE_EXTENSIONS:
        return "source_code", "content", "source_code_processor", 75, f"source extension: {ext}"

    if ext in DOCUMENT_EXTENSIONS:
        if role == "primary":
            return "primary_document", "primary", "document_processor", 100, f"primary document: {ext}"
        return "document", "content", "document_processor", 70, f"document extension: {ext}"

    if ext in IMAGE_EXTENSIONS:
        return "image_asset", "asset", "image_processor", 35, f"image extension: {ext}"

    if ext in DATA_EXTENSIONS:
        return "structured_data", "content", "structured_processor", 55, f"data extension: {ext}"

    if ext in ARCHIVE_EXTENSIONS:
        return "archive", "asset", "archive_processor", 40, f"archive extension: {ext}"

    if "/test" in lower_path or "/tests" in lower_path:
        return "test_file", "supporting", "source_code_processor", 65, "test path"

    return "unknown", "supporting", None, 10, "no membership rule matched"
