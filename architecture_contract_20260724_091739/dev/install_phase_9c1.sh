#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$PROJECT_ROOT"

echo
echo "======================================================================"
echo "JARVIS GEN 2 — PHASE IX-C1 COGNITIVE ARCHITECTURE INVENTORY"
echo "======================================================================"
echo

mkdir -p dev/tools
mkdir -p dev/verification
mkdir -p docs/architecture/convergence

cat > dev/tools/audit_cognitive_convergence.py <<'PYEOF'
#!/usr/bin/env python3
"""Audit competing JARVIS cognitive-engine implementations.

Phase IX-C1 is intentionally non-destructive. This tool inventories the
Executive package, competing planning implementations, cognitive architecture
documents, and whitepaper locations.

It does not move, rename, delete, or rewrite project source files.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import re
import sys
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Sequence


PROJECT_MARKERS = (
    ".git",
    "pyproject.toml",
    "requirements.txt",
    "setup.cfg",
)

PLANNING_LOCATIONS = (
    Path("core/executive/planner.py"),
    Path("core/executive/planning"),
    Path("core/executive/planning_engine"),
)

COGNITIVE_DOCUMENT_LOCATIONS = (
    Path("docs/architecture"),
    Path("docs/constitution"),
    Path("docs/specifications"),
    Path("docs/standards"),
    Path("docs/whitepapers"),
)

ROOT_WHITEPAPER_PATTERN = re.compile(
    r"^WP-(?P<number>\d{4})-(?P<slug>.+)\.md$",
    re.IGNORECASE,
)


@dataclass(frozen=True, slots=True)
class ImportRecord:
    module: str
    names: tuple[str, ...] = ()
    level: int = 0


@dataclass(frozen=True, slots=True)
class SymbolRecord:
    name: str
    kind: str
    line: int
    bases: tuple[str, ...] = ()
    decorators: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class PythonFileRecord:
    path: str
    sha256: str
    size_bytes: int
    line_count: int
    module_docstring: str
    imports: tuple[ImportRecord, ...]
    symbols: tuple[SymbolRecord, ...]
    all_exports: tuple[str, ...]
    syntax_valid: bool
    syntax_error: str | None = None


@dataclass(frozen=True, slots=True)
class DocumentRecord:
    path: str
    sha256: str
    size_bytes: int
    line_count: int
    title: str
    headings: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class WhitepaperDisposition:
    source_path: str
    proposed_destination: str
    destination_exists: bool
    source_sha256: str
    destination_sha256: str | None
    relationship: str


@dataclass(slots=True)
class AuditReport:
    schema_version: str
    generated_at_utc: str
    project_root: str
    git_branch: str | None
    executive_python_files: list[PythonFileRecord] = field(
        default_factory=list
    )
    planning_locations: dict[str, list[str]] = field(default_factory=dict)
    planning_location_symbols: dict[str, list[str]] = field(
        default_factory=dict
    )
    duplicate_symbols: dict[str, list[str]] = field(default_factory=dict)
    cognitive_documents: list[DocumentRecord] = field(default_factory=list)
    root_whitepapers: list[WhitepaperDisposition] = field(
        default_factory=list
    )
    findings: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Inventory JARVIS cognitive architecture without modifying it."
        )
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=None,
        help="Repository root. Defaults to automatic discovery.",
    )
    parser.add_argument(
        "--json-output",
        type=Path,
        default=Path(
            "docs/architecture/convergence/"
            "phase_9c1_inventory.json"
        ),
    )
    parser.add_argument(
        "--markdown-output",
        type=Path,
        default=Path(
            "docs/architecture/convergence/"
            "phase_9c1_inventory.md"
        ),
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help=(
            "Exit nonzero when the architecture cannot be inventoried "
            "safely."
        ),
    )
    return parser.parse_args()


def discover_project_root(start: Path) -> Path:
    current = start.resolve()

    for candidate in (current, *current.parents):
        if any((candidate / marker).exists() for marker in PROJECT_MARKERS):
            return candidate

    raise RuntimeError(
        f"Could not locate project root from {start}"
    )


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)

    return digest.hexdigest()


def read_text(path: Path) -> str:
    return path.read_text(
        encoding="utf-8",
        errors="replace",
    )


def dotted_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id

    if isinstance(node, ast.Attribute):
        parent = dotted_name(node.value)
        return f"{parent}.{node.attr}" if parent else node.attr

    if isinstance(node, ast.Call):
        return dotted_name(node.func)

    if isinstance(node, ast.Subscript):
        return dotted_name(node.value)

    return ast.dump(node, include_attributes=False)


def extract_all_exports(tree: ast.Module) -> tuple[str, ...]:
    exports: list[str] = []

    for node in tree.body:
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue

        targets: list[ast.expr] = []

        if isinstance(node, ast.Assign):
            targets.extend(node.targets)
            value = node.value
        else:
            targets.append(node.target)
            value = node.value

        if value is None:
            continue

        is_all = any(
            isinstance(target, ast.Name) and target.id == "__all__"
            for target in targets
        )

        if not is_all:
            continue

        if not isinstance(value, (ast.List, ast.Tuple, ast.Set)):
            continue

        for element in value.elts:
            if isinstance(element, ast.Constant) and isinstance(
                element.value,
                str,
            ):
                exports.append(element.value)

    return tuple(sorted(set(exports)))


def inspect_python_file(
    project_root: Path,
    path: Path,
) -> PythonFileRecord:
    relative_path = path.relative_to(project_root).as_posix()
    source = read_text(path)
    line_count = len(source.splitlines())

    try:
        tree = ast.parse(
            source,
            filename=relative_path,
        )
    except SyntaxError as exc:
        return PythonFileRecord(
            path=relative_path,
            sha256=sha256_file(path),
            size_bytes=path.stat().st_size,
            line_count=line_count,
            module_docstring="",
            imports=(),
            symbols=(),
            all_exports=(),
            syntax_valid=False,
            syntax_error=(
                f"{exc.msg} at line {exc.lineno}, "
                f"column {exc.offset}"
            ),
        )

    imports: list[ImportRecord] = []
    symbols: list[SymbolRecord] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.append(
                ImportRecord(
                    module="",
                    names=tuple(
                        alias.name
                        for alias in node.names
                    ),
                )
            )
        elif isinstance(node, ast.ImportFrom):
            imports.append(
                ImportRecord(
                    module=node.module or "",
                    names=tuple(
                        alias.name
                        for alias in node.names
                    ),
                    level=node.level,
                )
            )

    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            symbols.append(
                SymbolRecord(
                    name=node.name,
                    kind="class",
                    line=node.lineno,
                    bases=tuple(
                        dotted_name(base)
                        for base in node.bases
                    ),
                    decorators=tuple(
                        dotted_name(decorator)
                        for decorator in node.decorator_list
                    ),
                )
            )
        elif isinstance(
            node,
            (ast.FunctionDef, ast.AsyncFunctionDef),
        ):
            symbols.append(
                SymbolRecord(
                    name=node.name,
                    kind=(
                        "async_function"
                        if isinstance(node, ast.AsyncFunctionDef)
                        else "function"
                    ),
                    line=node.lineno,
                    decorators=tuple(
                        dotted_name(decorator)
                        for decorator in node.decorator_list
                    ),
                )
            )

    imports.sort(
        key=lambda item: (
            item.level,
            item.module,
            item.names,
        )
    )
    symbols.sort(
        key=lambda item: (
            item.line,
            item.name,
        )
    )

    return PythonFileRecord(
        path=relative_path,
        sha256=sha256_file(path),
        size_bytes=path.stat().st_size,
        line_count=line_count,
        module_docstring=ast.get_docstring(tree) or "",
        imports=tuple(imports),
        symbols=tuple(symbols),
        all_exports=extract_all_exports(tree),
        syntax_valid=True,
        syntax_error=None,
    )


def iter_python_files(path: Path) -> Iterable[Path]:
    if path.is_file() and path.suffix == ".py":
        yield path
        return

    if not path.is_dir():
        return

    yield from sorted(
        candidate
        for candidate in path.rglob("*.py")
        if "__pycache__" not in candidate.parts
    )


def inspect_document(
    project_root: Path,
    path: Path,
) -> DocumentRecord:
    source = read_text(path)
    headings = tuple(
        line.strip()
        for line in source.splitlines()
        if line.lstrip().startswith("#")
    )
    title = ""

    for heading in headings:
        title = heading.lstrip("#").strip()
        if title:
            break

    return DocumentRecord(
        path=path.relative_to(project_root).as_posix(),
        sha256=sha256_file(path),
        size_bytes=path.stat().st_size,
        line_count=len(source.splitlines()),
        title=title,
        headings=headings,
    )


def collect_git_branch(project_root: Path) -> str | None:
    head_path = project_root / ".git" / "HEAD"

    if not head_path.exists():
        return None

    content = read_text(head_path).strip()
    prefix = "ref: refs/heads/"

    if content.startswith(prefix):
        return content[len(prefix):]

    return content or None


def collect_planning_location(
    project_root: Path,
    location: Path,
) -> tuple[list[str], list[str]]:
    absolute = project_root / location
    files: list[str] = []
    symbols: list[str] = []

    for python_file in iter_python_files(absolute):
        record = inspect_python_file(
            project_root,
            python_file,
        )
        files.append(record.path)

        for symbol in record.symbols:
            symbols.append(
                f"{symbol.kind}:{symbol.name}@{record.path}:{symbol.line}"
            )

    return sorted(files), sorted(symbols)


def find_duplicate_symbols(
    records: Sequence[PythonFileRecord],
) -> dict[str, list[str]]:
    locations: dict[str, list[str]] = defaultdict(list)

    for record in records:
        for symbol in record.symbols:
            if symbol.name.startswith("_"):
                continue

            locations[symbol.name].append(
                f"{record.path}:{symbol.line} ({symbol.kind})"
            )

    return {
        name: sorted(entries)
        for name, entries in sorted(locations.items())
        if len(entries) > 1
    }


def classify_whitepaper_relationship(
    source: Path,
    destination: Path,
) -> tuple[str, str | None]:
    if not destination.exists():
        return "destination_missing", None

    source_hash = sha256_file(source)
    destination_hash = sha256_file(destination)

    if source_hash == destination_hash:
        return "identical_duplicate", destination_hash

    source_text = read_text(source).strip()
    destination_text = read_text(destination).strip()

    if source_text == destination_text:
        return "textually_identical", destination_hash

    if source_text and source_text in destination_text:
        return "source_contained_in_destination", destination_hash

    if destination_text and destination_text in source_text:
        return "destination_contained_in_source", destination_hash

    return "different_content", destination_hash


def collect_root_whitepapers(
    project_root: Path,
) -> list[WhitepaperDisposition]:
    dispositions: list[WhitepaperDisposition] = []

    for source in sorted(project_root.glob("WP-*.md")):
        match = ROOT_WHITEPAPER_PATTERN.match(source.name)

        if match is None:
            proposed_name = source.name
        else:
            proposed_name = (
                f"WP-{match.group('number')}-"
                f"{match.group('slug')}.md"
            )

        destination = (
            project_root
            / "docs"
            / "whitepapers"
            / proposed_name
        )
        relationship, destination_hash = (
            classify_whitepaper_relationship(
                source,
                destination,
            )
        )

        dispositions.append(
            WhitepaperDisposition(
                source_path=source.relative_to(
                    project_root
                ).as_posix(),
                proposed_destination=destination.relative_to(
                    project_root
                ).as_posix(),
                destination_exists=destination.exists(),
                source_sha256=sha256_file(source),
                destination_sha256=destination_hash,
                relationship=relationship,
            )
        )

    return dispositions


def build_findings(
    report: AuditReport,
) -> None:
    existing_locations = {
        location: files
        for location, files in report.planning_locations.items()
        if files
    }

    if len(existing_locations) > 1:
        report.findings.append(
            "Multiple planning implementations are present: "
            + ", ".join(sorted(existing_locations))
        )

    if report.duplicate_symbols:
        report.findings.append(
            f"{len(report.duplicate_symbols)} public symbol names appear "
            "in more than one Executive module."
        )

    invalid_files = [
        record.path
        for record in report.executive_python_files
        if not record.syntax_valid
    ]

    if invalid_files:
        report.findings.append(
            "Python syntax errors were detected in: "
            + ", ".join(invalid_files)
        )

    differing_whitepapers = [
        item.source_path
        for item in report.root_whitepapers
        if item.relationship == "different_content"
    ]

    if differing_whitepapers:
        report.findings.append(
            "Root-level whitepapers differ from their proposed canonical "
            "destinations: "
            + ", ".join(differing_whitepapers)
        )

    missing_whitepaper_destinations = [
        item.source_path
        for item in report.root_whitepapers
        if item.relationship == "destination_missing"
    ]

    if missing_whitepaper_destinations:
        report.findings.append(
            "Root-level whitepapers do not yet have canonical destination "
            "files: "
            + ", ".join(missing_whitepaper_destinations)
        )

    report.recommendations.extend(
        (
            "Do not remove planner.py, planning/, or planning_engine/ "
            "until Phase IX-C2 assigns canonical ownership.",
            "Treat core/executive/planning/ as the leading canonical "
            "candidate because it already contains service, repository, "
            "validation, dependency, model, enum, and error layers.",
            "Compare planning_engine models and enums against planning/ "
            "before merging their contracts.",
            "Keep the Executive package responsible for orchestration, "
            "not detailed planning algorithms.",
            "Reconcile root-level whitepapers by content and hash rather "
            "than filename alone.",
            "Introduce the reasoning engine only after canonical planning "
            "contracts and Executive public exports are stable.",
        )
    )


def build_report(project_root: Path) -> AuditReport:
    executive_root = project_root / "core" / "executive"

    executive_records = [
        inspect_python_file(project_root, path)
        for path in iter_python_files(executive_root)
    ]

    planning_locations: dict[str, list[str]] = {}
    planning_symbols: dict[str, list[str]] = {}

    for location in PLANNING_LOCATIONS:
        files, symbols = collect_planning_location(
            project_root,
            location,
        )
        planning_locations[location.as_posix()] = files
        planning_symbols[location.as_posix()] = symbols

    documents: list[DocumentRecord] = []

    for location in COGNITIVE_DOCUMENT_LOCATIONS:
        absolute = project_root / location

        if not absolute.exists():
            continue

        for path in sorted(absolute.rglob("*.md")):
            documents.append(
                inspect_document(project_root, path)
            )

    report = AuditReport(
        schema_version="1.0",
        generated_at_utc=datetime.now(
            timezone.utc
        ).isoformat(),
        project_root=project_root.as_posix(),
        git_branch=collect_git_branch(project_root),
        executive_python_files=executive_records,
        planning_locations=planning_locations,
        planning_location_symbols=planning_symbols,
        duplicate_symbols=find_duplicate_symbols(
            executive_records
        ),
        cognitive_documents=documents,
        root_whitepapers=collect_root_whitepapers(
            project_root
        ),
    )

    build_findings(report)
    return report


def serialize_report(report: AuditReport) -> dict[str, Any]:
    return asdict(report)


def markdown_table(
    headers: Sequence[str],
    rows: Sequence[Sequence[str]],
) -> list[str]:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]

    for row in rows:
        escaped = [
            str(value).replace("|", "\\|").replace("\n", " ")
            for value in row
        ]
        lines.append(
            "| " + " | ".join(escaped) + " |"
        )

    return lines


def render_markdown(report: AuditReport) -> str:
    lines: list[str] = [
        "# Phase IX-C1 Cognitive Architecture Inventory",
        "",
        "## Audit metadata",
        "",
        f"- Schema version: `{report.schema_version}`",
        f"- Generated: `{report.generated_at_utc}`",
        f"- Branch: `{report.git_branch or 'unknown'}`",
        f"- Project root: `{report.project_root}`",
        "",
        "## Executive package summary",
        "",
        (
            f"- Python files: "
            f"`{len(report.executive_python_files)}`"
        ),
        (
            f"- Public duplicate symbol names: "
            f"`{len(report.duplicate_symbols)}`"
        ),
        "",
    ]

    file_rows = []

    for record in report.executive_python_files:
        public_symbols = [
            symbol.name
            for symbol in record.symbols
            if not symbol.name.startswith("_")
        ]
        file_rows.append(
            (
                record.path,
                str(record.line_count),
                "yes" if record.syntax_valid else "no",
                ", ".join(public_symbols) or "—",
                record.sha256[:12],
            )
        )

    lines.extend(
        markdown_table(
            (
                "File",
                "Lines",
                "Syntax",
                "Public symbols",
                "SHA-256",
            ),
            file_rows,
        )
    )

    lines.extend(
        (
            "",
            "## Planning implementation locations",
            "",
        )
    )

    for location in PLANNING_LOCATIONS:
        key = location.as_posix()
        files = report.planning_locations.get(key, [])
        symbols = report.planning_location_symbols.get(
            key,
            [],
        )

        lines.append(f"### `{key}`")
        lines.append("")
        lines.append(f"- Files: `{len(files)}`")
        lines.append(f"- Symbols: `{len(symbols)}`")
        lines.append("")

        if files:
            for path in files:
                lines.append(f"- `{path}`")
        else:
            lines.append("- Not present.")

        lines.append("")

    lines.extend(
        (
            "## Duplicate public symbols",
            "",
        )
    )

    if report.duplicate_symbols:
        for name, locations in report.duplicate_symbols.items():
            lines.append(f"### `{name}`")
            lines.append("")
            for location in locations:
                lines.append(f"- `{location}`")
            lines.append("")
    else:
        lines.append("No duplicate public symbols detected.")
        lines.append("")

    lines.extend(
        (
            "## Root-level whitepaper disposition",
            "",
        )
    )

    whitepaper_rows = [
        (
            item.source_path,
            item.proposed_destination,
            item.relationship,
            item.source_sha256[:12],
            (
                item.destination_sha256[:12]
                if item.destination_sha256
                else "—"
            ),
        )
        for item in report.root_whitepapers
    ]

    if whitepaper_rows:
        lines.extend(
            markdown_table(
                (
                    "Source",
                    "Proposed destination",
                    "Relationship",
                    "Source hash",
                    "Destination hash",
                ),
                whitepaper_rows,
            )
        )
    else:
        lines.append("No root-level whitepapers detected.")

    lines.extend(
        (
            "",
            "## Findings",
            "",
        )
    )

    if report.findings:
        for finding in report.findings:
            lines.append(f"- {finding}")
    else:
        lines.append("- No structural conflicts detected.")

    lines.extend(
        (
            "",
            "## Recommendations",
            "",
        )
    )

    for recommendation in report.recommendations:
        lines.append(f"- {recommendation}")

    lines.extend(
        (
            "",
            "## IX-C1 decision",
            "",
            (
                "This report is an inventory only. No implementation is "
                "declared canonical by IX-C1."
            ),
            "",
            (
                "Canonical ownership, file migration, compatibility "
                "adapters, and deletion decisions belong to Phase IX-C2."
            ),
            "",
        )
    )

    return "\n".join(lines)


def write_outputs(
    project_root: Path,
    report: AuditReport,
    json_output: Path,
    markdown_output: Path,
) -> None:
    json_path = (
        json_output
        if json_output.is_absolute()
        else project_root / json_output
    )
    markdown_path = (
        markdown_output
        if markdown_output.is_absolute()
        else project_root / markdown_output
    )

    json_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    markdown_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    json_path.write_text(
        json.dumps(
            serialize_report(report),
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    markdown_path.write_text(
        render_markdown(report),
        encoding="utf-8",
    )

    print(
        f"JSON report     : "
        f"{json_path.relative_to(project_root)}"
    )
    print(
        f"Markdown report : "
        f"{markdown_path.relative_to(project_root)}"
    )


def validate_report(report: AuditReport) -> list[str]:
    failures: list[str] = []

    if not report.executive_python_files:
        failures.append(
            "No Executive Python files were discovered."
        )

    invalid_python = [
        record.path
        for record in report.executive_python_files
        if not record.syntax_valid
    ]

    if invalid_python:
        failures.append(
            "Syntax-invalid Executive files: "
            + ", ".join(invalid_python)
        )

    expected_locations = {
        location.as_posix()
        for location in PLANNING_LOCATIONS
    }

    if set(report.planning_locations) != expected_locations:
        failures.append(
            "Planning location inventory is incomplete."
        )

    return failures


def main() -> int:
    arguments = parse_arguments()
    project_root = (
        arguments.project_root.resolve()
        if arguments.project_root is not None
        else discover_project_root(Path.cwd())
    )

    report = build_report(project_root)

    write_outputs(
        project_root=project_root,
        report=report,
        json_output=arguments.json_output,
        markdown_output=arguments.markdown_output,
    )

    print()
    print(
        f"Executive files : "
        f"{len(report.executive_python_files)}"
    )
    print(
        f"Duplicate names  : "
        f"{len(report.duplicate_symbols)}"
    )
    print(
        f"Architecture docs: "
        f"{len(report.cognitive_documents)}"
    )
    print(
        f"Root whitepapers : "
        f"{len(report.root_whitepapers)}"
    )

    if arguments.check:
        failures = validate_report(report)

        if failures:
            print()
            print("Audit validation failed:", file=sys.stderr)

            for failure in failures:
                print(
                    f"  - {failure}",
                    file=sys.stderr,
                )

            return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
PYEOF

cat > dev/verification/verify_cognitive_convergence_inventory.py <<'PYEOF'
#!/usr/bin/env python3
"""Verify the Phase IX-C1 cognitive convergence inventory."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


REQUIRED_TOP_LEVEL_KEYS = {
    "schema_version",
    "generated_at_utc",
    "project_root",
    "git_branch",
    "executive_python_files",
    "planning_locations",
    "planning_location_symbols",
    "duplicate_symbols",
    "cognitive_documents",
    "root_whitepapers",
    "findings",
    "recommendations",
}

EXPECTED_PLANNING_LOCATIONS = {
    "core/executive/planner.py",
    "core/executive/planning",
    "core/executive/planning_engine",
}


def load_json(path: Path) -> dict[str, Any]:
    with path.open(
        "r",
        encoding="utf-8",
    ) as handle:
        payload = json.load(handle)

    if not isinstance(payload, dict):
        raise ValueError(
            "Inventory JSON root must be an object"
        )

    return payload


def main() -> int:
    project_root = Path(__file__).resolve().parents[2]
    report_path = (
        project_root
        / "docs"
        / "architecture"
        / "convergence"
        / "phase_9c1_inventory.json"
    )
    markdown_path = (
        project_root
        / "docs"
        / "architecture"
        / "convergence"
        / "phase_9c1_inventory.md"
    )

    failures: list[str] = []

    if not report_path.is_file():
        failures.append(
            f"Missing JSON inventory: {report_path}"
        )

    if not markdown_path.is_file():
        failures.append(
            f"Missing Markdown inventory: {markdown_path}"
        )

    if failures:
        for failure in failures:
            print(f"[FAIL] {failure}")

        return 1

    try:
        payload = load_json(report_path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"[FAIL] Could not read inventory: {exc}")
        return 1

    missing_keys = REQUIRED_TOP_LEVEL_KEYS - set(payload)

    if missing_keys:
        failures.append(
            "Missing report keys: "
            + ", ".join(sorted(missing_keys))
        )

    executive_files = payload.get(
        "executive_python_files",
        [],
    )

    if not isinstance(executive_files, list):
        failures.append(
            "executive_python_files must be a list"
        )
    elif not executive_files:
        failures.append(
            "No Executive Python files were inventoried"
        )
    else:
        invalid_files = [
            record.get("path", "<unknown>")
            for record in executive_files
            if not record.get("syntax_valid", False)
        ]

        if invalid_files:
            failures.append(
                "Syntax-invalid Executive files: "
                + ", ".join(invalid_files)
            )

    planning_locations = payload.get(
        "planning_locations",
        {},
    )

    if not isinstance(planning_locations, dict):
        failures.append(
            "planning_locations must be an object"
        )
    else:
        missing_locations = (
            EXPECTED_PLANNING_LOCATIONS
            - set(planning_locations)
        )

        if missing_locations:
            failures.append(
                "Missing planning inventory locations: "
                + ", ".join(sorted(missing_locations))
            )

    recommendations = payload.get(
        "recommendations",
        [],
    )

    if not isinstance(recommendations, list) or not recommendations:
        failures.append(
            "The audit produced no recommendations"
        )

    markdown_text = markdown_path.read_text(
        encoding="utf-8",
        errors="replace",
    )

    required_markdown_sections = (
        "# Phase IX-C1 Cognitive Architecture Inventory",
        "## Planning implementation locations",
        "## Duplicate public symbols",
        "## Root-level whitepaper disposition",
        "## Recommendations",
    )

    for section in required_markdown_sections:
        if section not in markdown_text:
            failures.append(
                f"Missing Markdown section: {section}"
            )

    if failures:
        for failure in failures:
            print(f"[FAIL] {failure}")

        return 1

    print(
        "[PASS] Cognitive convergence inventory "
        "is complete and structurally valid"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
PYEOF

cat > dev/verify_phase_9c1.sh <<'SH_EOF'
#!/usr/bin/env bash
set -uo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python}"

cd "$PROJECT_ROOT"

PASSED=0
FAILED=0
LOG_FILE="/tmp/jarvis_phase_9c1_check.log"

pass() {
    printf '[PASS] %s\n' "$1"
    PASSED=$((PASSED + 1))
}

fail() {
    printf '[FAIL] %s\n' "$1"
    FAILED=$((FAILED + 1))
}

run_check() {
    local description="$1"
    shift

    if "$@" >"$LOG_FILE" 2>&1; then
        pass "$description"
    else
        fail "$description"
        cat "$LOG_FILE"
    fi
}

echo
echo "======================================================================"
echo "JARVIS GEN 2 — PHASE IX-C1 COGNITIVE ARCHITECTURE INVENTORY"
echo "======================================================================"

run_check \
    "Audit-tool compilation" \
    "$PYTHON_BIN" -m py_compile \
    dev/tools/audit_cognitive_convergence.py \
    dev/verification/verify_cognitive_convergence_inventory.py

run_check \
    "Executive package compilation" \
    "$PYTHON_BIN" -m compileall -q core/executive

run_check \
    "Non-destructive cognitive architecture audit" \
    "$PYTHON_BIN" dev/tools/audit_cognitive_convergence.py \
    --check

run_check \
    "Generated inventory structural verification" \
    "$PYTHON_BIN" \
    dev/verification/verify_cognitive_convergence_inventory.py

run_check \
    "Inventory JSON parses successfully" \
    "$PYTHON_BIN" -m json.tool \
    docs/architecture/convergence/phase_9c1_inventory.json

run_check \
    "No Python cache files under Executive source" \
    bash -c \
    '! find core/executive \( -type d -name "__pycache__" -o -type f -name "*.pyc" \) -print -quit | grep -q .'

run_check \
    "Audit contains all planning candidates" \
    "$PYTHON_BIN" -c '
import json
from pathlib import Path

path = Path(
    "docs/architecture/convergence/"
    "phase_9c1_inventory.json"
)
data = json.loads(path.read_text(encoding="utf-8"))

expected = {
    "core/executive/planner.py",
    "core/executive/planning",
    "core/executive/planning_engine",
}

actual = set(data["planning_locations"])

missing = expected - actual

if missing:
    raise SystemExit(
        "Missing planning candidates: "
        + ", ".join(sorted(missing))
    )
'

echo "----------------------------------------------------------------------"
printf 'Checks passed : %d\n' "$PASSED"
printf 'Checks failed : %d\n' "$FAILED"

if [ "$FAILED" -eq 0 ]; then
    echo "Overall status: EXCELLENT"
    echo "======================================================================"
    exit 0
fi

echo "Overall status: FAILED"
echo "======================================================================"
exit 1
SH_EOF

cat > docs/architecture/convergence/README.md <<'MDEOF'
# Cognitive Architecture Convergence

This directory records the controlled reconciliation of JARVIS cognitive
architecture and implementation.

## Purpose

JARVIS currently contains multiple generations of Executive and planning
code, together with an expanded constitutional, architectural, specification,
standards, and whitepaper corpus.

The convergence phases prevent destructive cleanup and architectural drift.

## Phase structure

### IX-C1 — Inventory and Preservation

- Preserve the existing workspace.
- Inventory competing implementations.
- Record public symbols and imports.
- Record source hashes.
- Detect duplicate public names.
- Compare root-level whitepapers with canonical documentation locations.
- Make no destructive source changes.

### IX-C2 — Canonical Ownership

- Assign canonical ownership to planning components.
- Define the stable Planning Engine public interface.
- Determine the role of legacy `planner.py`.
- Determine whether `planning_engine/` contributes contracts or should be
  superseded.
- Define compatibility boundaries.

### IX-C3 — Controlled Migration

- Move reusable implementation into canonical packages.
- Add compatibility imports where necessary.
- Update Executive orchestration.
- Update tests and verification.
- Remove obsolete code only after regression verification.

### IX-C4 — Architecture Freeze

- Freeze canonical cognitive subsystem boundaries.
- Record architectural fingerprints.
- Update subsystem ownership documentation.
- Permit Reasoning Engine implementation to begin.

## Governing rule

No file is deleted merely because another file has a similar name.

Deletion requires:

1. content comparison;
2. ownership determination;
3. dependency analysis;
4. migration or compatibility coverage;
5. regression verification;
6. recorded architectural justification.
MDEOF

chmod +x dev/install_phase_9c1.sh
chmod +x dev/tools/audit_cognitive_convergence.py
chmod +x dev/verification/verify_cognitive_convergence_inventory.py
chmod +x dev/verify_phase_9c1.sh

echo
echo "Created:"
echo "  dev/tools/audit_cognitive_convergence.py"
echo "  dev/verification/verify_cognitive_convergence_inventory.py"
echo "  dev/verify_phase_9c1.sh"
echo "  docs/architecture/convergence/README.md"
echo
echo "Phase IX-C1 installation completed."
echo
