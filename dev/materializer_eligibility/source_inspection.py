from __future__ import annotations
import ast, re
from pathlib import Path
from typing import Any

EXT_RE = re.compile(r"\.[a-z0-9]{1,8}", re.I)

def inspect_materializer_source(project_root: Path) -> dict[str, Any]:
    candidates = (
        project_root / "core/knowledge_catalog/materialization/engine.py",
        project_root / "core/knowledge_catalog/materialization/cli.py",
        project_root / "core/knowledge_catalog/materialization/search.py",
        project_root / "core/knowledge_catalog/backfill.py",
    )
    result: dict[str, Any] = {
        "files": [],
        "supported_extensions": [],
        "selection_functions": [],
        "filters": [],
        "size_limits": [],
        "errors": [],
    }
    extensions = set()
    functions = set()
    filters = set()
    size_limits = set()

    for path in candidates:
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        result["files"].append(str(path))
        extensions.update(
            token.casefold()
            for token in EXT_RE.findall(text)
            if token.casefold() in {
                ".pdf", ".md", ".txt", ".html", ".htm",
                ".docx", ".epub", ".json", ".csv", ".xml",
            }
        )
        try:
            tree = ast.parse(text)
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    name = node.name.casefold()
                    if any(token in name for token in (
                        "candidate", "material", "extract", "select",
                        "eligible", "discover", "chunk",
                    )):
                        functions.add(node.name)
                if isinstance(node, ast.Compare):
                    source = ast.get_source_segment(text, node)
                    if source and any(token in source.casefold() for token in (
                        "suffix", "extension", "media_type", "mime",
                        "size", "exists", "sha256", "status",
                    )):
                        filters.add(source.strip())
                if isinstance(node, ast.Assign):
                    source = ast.get_source_segment(text, node)
                    if source and any(token in source.casefold() for token in (
                        "max_size", "size_limit", "target_chunk",
                    )):
                        size_limits.add(source.strip())
        except SyntaxError as exc:
            result["errors"].append(f"{path}: {exc}")

    result["supported_extensions"] = sorted(extensions)
    result["selection_functions"] = sorted(functions)
    result["filters"] = sorted(filters)[:100]
    result["size_limits"] = sorted(size_limits)
    return result
