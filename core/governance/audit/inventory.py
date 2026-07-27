from __future__ import annotations

import hashlib
import json
from pathlib import Path

from .filesystem import DeterministicFilesystemScanner
from .markdown_parser import DeterministicMarkdownParser
from .models import EvidenceClass, FileKind, ParseDiagnostic, RepositoryInventory, RepositoryStatistics, to_primitive
from .python_parser import AstPythonParser


SCHEMA_VERSION = "1.1.0"


class RepositoryInventoryBuilder:
    def __init__(self, filesystem_scanner=None, python_parser=None, markdown_parser=None) -> None:
        self._filesystem = filesystem_scanner or DeterministicFilesystemScanner()
        self._python = python_parser or AstPythonParser()
        self._markdown = markdown_parser or DeterministicMarkdownParser()

    def build(self, root: Path, output_directory: Path | None = None) -> RepositoryInventory:
        root = root.expanduser().resolve()
        files = self._filesystem.scan(root)
        python_modules = []
        markdown_documents = []
        diagnostics: list[ParseDiagnostic] = []
        for file in files:
            if file.kind is FileKind.PYTHON:
                module = self._python.parse(root, file)
                python_modules.append(module)
                diagnostics.extend(module.diagnostics)
            elif file.kind is FileKind.MARKDOWN:
                document = self._markdown.parse(root, file)
                markdown_documents.append(document)
                diagnostics.extend(document.diagnostics)
        python_modules.sort(key=lambda item: item.path)
        markdown_documents.sort(key=lambda item: item.path)
        diagnostics.sort(key=lambda item: (item.path, item.parser, item.line or 0, item.message))
        statistics = _build_statistics(files, python_modules, markdown_documents, diagnostics)
        provisional = {
            "schema_version": SCHEMA_VERSION, "root_name": root.name, "files": to_primitive(files),
            "python_modules": to_primitive(tuple(python_modules)),
            "markdown_documents": to_primitive(tuple(markdown_documents)),
            "diagnostics": to_primitive(tuple(diagnostics)), "statistics": to_primitive(statistics),
        }
        fingerprint = _fingerprint(provisional)
        inventory = RepositoryInventory(
            schema_version=SCHEMA_VERSION, root_name=root.name, files=files,
            python_modules=tuple(python_modules), markdown_documents=tuple(markdown_documents),
            diagnostics=tuple(diagnostics), statistics=statistics, fingerprint=fingerprint,
        )
        if output_directory is not None:
            self.write_outputs(inventory, output_directory)
        return inventory

    def write_outputs(self, inventory: RepositoryInventory, output_directory: Path) -> None:
        output_directory.mkdir(parents=True, exist_ok=True)
        _write_json(output_directory / "repository_inventory.json", to_primitive(inventory))
        _write_json(output_directory / "repository_statistics.json", to_primitive(inventory.statistics))
        _write_json(output_directory / "documentation_inventory.json", {
            "schema_version": inventory.schema_version, "root_name": inventory.root_name,
            "documents": to_primitive(inventory.markdown_documents),
            "fingerprint": _fingerprint(to_primitive(inventory.markdown_documents)),
        })


def _build_statistics(files, python_modules, markdown_documents, diagnostics) -> RepositoryStatistics:
    return RepositoryStatistics(
        total_files=len(files), total_bytes=sum(item.size_bytes for item in files),
        python_files=sum(item.kind is FileKind.PYTHON for item in files),
        markdown_files=sum(item.kind is FileKind.MARKDOWN for item in files),
        shell_files=sum(item.kind is FileKind.SHELL for item in files),
        package_markers=sum(item.is_package_marker for item in files), test_files=sum(item.is_test for item in files),
        verification_files=sum(item.is_verification for item in files),
        architecture_documents=sum(item.is_architecture_document for item in files),
        adr_documents=sum(item.is_adr for item in files),
        constitutional_documents=sum(item.is_constitutional_document for item in files),
        whitepapers=sum(item.is_whitepaper for item in files), python_modules=len(python_modules),
        python_symbols=sum(len(item.symbols) for item in python_modules),
        markdown_documents=len(markdown_documents), diagnostics=len(diagnostics),
        source_files=sum(item.evidence_class is EvidenceClass.SOURCE for item in files),
        generated_files=sum(item.evidence_class is EvidenceClass.GENERATED for item in files),
        external_files=sum(item.evidence_class is EvidenceClass.EXTERNAL for item in files),
    )


def _canonical_json(value) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def _fingerprint(value) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, sort_keys=True, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
