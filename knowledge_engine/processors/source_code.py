from __future__ import annotations

import ast
from pathlib import Path

from knowledge_engine.processors.base import BaseProcessor, ProcessorResult


class SourceCodeProcessor(BaseProcessor):
    name = "source_code_processor"
    content_type = "source_code"

    extensions = {
        ".py", ".pyw", ".java", ".c", ".h", ".cpp", ".hpp", ".cc", ".cxx",
        ".cs", ".rs", ".go", ".js", ".jsx", ".ts", ".tsx", ".php", ".rb",
        ".swift", ".kt", ".scala", ".sh", ".ps1", ".sql", ".asm",
    }

    filenames = {"Makefile", "CMakeLists.txt", "Dockerfile"}

    def process(self, path: Path) -> ProcessorResult:
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
            metadata = {
                "extension": path.suffix.lower(),
                "filename": path.name,
                "language": self._detect_language(path),
            }

            if path.suffix.lower() == ".py":
                metadata.update(self._python_metadata(text))

            return ProcessorResult(
                file_path=str(path),
                processor=self.name,
                content_type=self.content_type,
                text=text,
                metadata=metadata,
                status="processed" if text else "empty",
                error=None if text else "empty source file",
            )
        except Exception as exc:
            return ProcessorResult(
                file_path=str(path),
                processor=self.name,
                content_type=self.content_type,
                text="",
                metadata={"extension": path.suffix.lower(), "filename": path.name},
                status="failed",
                error=str(exc),
            )

    def _detect_language(self, path: Path) -> str:
        if path.name == "Makefile":
            return "make"
        if path.name == "CMakeLists.txt":
            return "cmake"
        if path.name == "Dockerfile":
            return "dockerfile"

        return {
            ".py": "python", ".pyw": "python", ".java": "java",
            ".c": "c", ".h": "c/c++ header", ".cpp": "cpp",
            ".hpp": "cpp header", ".cc": "cpp", ".cxx": "cpp",
            ".cs": "csharp", ".rs": "rust", ".go": "go",
            ".js": "javascript", ".jsx": "javascript/react",
            ".ts": "typescript", ".tsx": "typescript/react",
            ".php": "php", ".rb": "ruby", ".swift": "swift",
            ".kt": "kotlin", ".scala": "scala", ".sh": "shell",
            ".ps1": "powershell", ".sql": "sql", ".asm": "assembly",
        }.get(path.suffix.lower(), "unknown")

    def _python_metadata(self, text: str) -> dict:
        try:
            tree = ast.parse(text)
        except Exception:
            return {"python_parseable": False, "functions": [], "classes": [], "imports": []}

        functions, classes, imports = [], [], []

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                functions.append(node.name)
            elif isinstance(node, ast.ClassDef):
                classes.append(node.name)
            elif isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.append(node.module)

        return {
            "python_parseable": True,
            "functions": functions,
            "classes": classes,
            "imports": sorted(set(imports)),
        }
