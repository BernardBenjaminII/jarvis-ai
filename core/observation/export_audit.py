"""Observation public-export inventory."""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True, slots=True)
class ObservationExport:
    path: str
    imported_from: str
    alias: str
    export_kind: str = "reexport"


def module_defines_observation(path: Path) -> bool:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (OSError, SyntaxError, UnicodeDecodeError):
        return False

    return any(
        isinstance(node, ast.ClassDef) and node.name == "Observation"
        for node in tree.body
    )


def scan_observation_exports(
    root: Path | str,
    *,
    search_roots: Iterable[str] = ("core",),
) -> tuple[ObservationExport, ...]:
    root_path = Path(root).resolve()
    exports: list[ObservationExport] = []

    for search_root in search_roots:
        base = root_path / search_root
        if not base.exists():
            continue

        for path in sorted(base.rglob("*.py")):
            if "__pycache__" in path.parts:
                continue

            try:
                tree = ast.parse(
                    path.read_text(encoding="utf-8"),
                    filename=str(path),
                )
            except (OSError, SyntaxError, UnicodeDecodeError):
                continue

            for node in tree.body:
                if isinstance(node, ast.ImportFrom):
                    for imported in node.names:
                        if imported.name == "Observation":
                            exports.append(
                                ObservationExport(
                                    path=path.relative_to(root_path).as_posix(),
                                    imported_from=node.module or "",
                                    alias=imported.asname or imported.name,
                                )
                            )
                elif isinstance(node, ast.Import):
                    for imported in node.names:
                        if imported.asname == "Observation":
                            exports.append(
                                ObservationExport(
                                    path=path.relative_to(root_path).as_posix(),
                                    imported_from=imported.name,
                                    alias=imported.asname,
                                    export_kind="import_alias",
                                )
                            )

    return tuple(
        sorted(
            exports,
            key=lambda item: (
                item.path,
                item.imported_from,
                item.alias,
                item.export_kind,
            ),
        )
    )
