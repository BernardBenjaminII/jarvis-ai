from __future__ import annotations

import ast
import json
import re
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class FileRepair:
    path: str
    status: str
    replacements: int
    details: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def read_resolved_hook(root: Path) -> str:
    graph_json = (
        root
        / "docs/audits/genesis_ix_a4_3c/runtime_call_graph.json"
    )

    if graph_json.is_file():
        data = json.loads(graph_json.read_text(encoding="utf-8"))
        method = (
            data.get("director_hook", {}).get("method")
        )
        if method:
            return str(method)

    summary = (
        root
        / "docs/audits/genesis_ix_a4_3c/reconstruction_summary.md"
    )

    if summary.is_file():
        match = re.search(
            r"Actual Director hook is ['`](?P<method>[A-Za-z_][A-Za-z0-9_]*)['`]",
            summary.read_text(encoding="utf-8"),
        )
        if match:
            return match.group("method")

    contract = (
        root
        / "docs/audits/genesis_ix_a4_3c/"
        "ix_a4_3b_hook_repair_contract.md"
    )

    if contract.is_file():
        text = contract.read_text(encoding="utf-8")
        match = re.search(
            r"resolved callable.*?\b(?P<method>submit|dispatch|direct|route|plan)\b",
            text,
            re.IGNORECASE | re.DOTALL,
        )
        if match:
            return match.group("method")

    raise RuntimeError(
        "Unable to resolve the ExecutiveDirector hook from IX-A4.3C."
    )


def director_execute_calls(path: Path) -> list[int]:
    try:
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source)
    except Exception:
        return []

    lines: list[int] = []

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue

        function = node.func

        if (
            isinstance(function, ast.Attribute)
            and function.attr == "execute"
            and isinstance(function.value, ast.Name)
            and function.value.id == "director"
        ):
            lines.append(node.lineno)

        if (
            isinstance(function, ast.Attribute)
            and function.attr == "execute"
            and isinstance(function.value, ast.Attribute)
            and function.value.attr == "director"
        ):
            lines.append(node.lineno)

    return lines


def repair_gap_tracer(
    root: Path,
    resolved_method: str,
) -> FileRepair:
    path = root / "core/retrieval/gap_trace/tracer.py"

    if not path.is_file():
        return FileRepair(
            path=str(path),
            status="absent",
            replacements=0,
            details=("IX-A4.3B tracer is not installed.",),
        )

    source = path.read_text(encoding="utf-8")
    original = source
    details: list[str] = []

    import_line = (
        "from core.executive.director_dispatch "
        "import resolve_director_dispatch\n"
    )

    if import_line.strip() not in source:
        future = "from __future__ import annotations\n"

        if future not in source:
            raise RuntimeError(
                "IX-A4.3B tracer lacks the expected future import."
            )

        source = source.replace(
            future,
            future + "\n" + import_line,
            1,
        )
        details.append("Added canonical Director dispatch resolver import.")

    patterns = (
        (
            "original_execute = director.execute",
            (
                "resolved_director = resolve_director_dispatch(\n"
                "            director,\n"
                f"            preferred={resolved_method!r},\n"
                "        )\n"
                "        original_execute = resolved_director.callable"
            ),
        ),
        (
            'patch(director, "execute", traced_execute)',
            (
                "patch(\n"
                "            director,\n"
                "            resolved_director.method_name,\n"
                "            traced_execute,\n"
                "        )"
            ),
        ),
    )

    replacements = 0

    for old, new in patterns:
        if old in source:
            source = source.replace(old, new, 1)
            replacements += 1
            details.append(f"Replaced hard-coded expression: {old}")

    if (
        "resolved_director = resolve_director_dispatch(" not in source
        and "director.execute" not in source
    ):
        details.append(
            "Tracer contains no hard-coded director.execute assumption."
        )

    if source != original:
        path.write_text(source, encoding="utf-8")
        status = "repaired"
    else:
        status = "unchanged"

    return FileRepair(
        path=str(path),
        status=status,
        replacements=replacements,
        details=tuple(details),
    )


def repair_production_calls(
    root: Path,
    resolved_method: str,
) -> list[FileRepair]:
    results: list[FileRepair] = []

    for path in sorted((root / "core").rglob("*.py")):
        if any(
            part in {
                "tests",
                "__pycache__",
                "failure_analysis",
                "call_graph",
                "gap_trace",
            }
            for part in path.parts
        ):
            continue

        lines = director_execute_calls(path)

        if not lines:
            continue

        source = path.read_text(encoding="utf-8")
        repaired = source.replace(
            "director.execute(",
            f"director.{resolved_method}(",
        ).replace(
            "self.director.execute(",
            f"self.director.{resolved_method}(",
        )

        replacement_count = (
            source.count("director.execute(")
            + source.count("self.director.execute(")
        )

        if repaired == source:
            results.append(
                FileRepair(
                    path=str(path),
                    status="detected_not_repaired",
                    replacements=0,
                    details=(
                        f"AST detected calls at lines {lines}.",
                        "No exact safe textual replacement matched.",
                    ),
                )
            )
            continue

        path.write_text(repaired, encoding="utf-8")

        results.append(
            FileRepair(
                path=str(path),
                status="repaired",
                replacements=replacement_count,
                details=(
                    f"Replaced confirmed Director execute calls at lines {lines}.",
                    f"Canonical method: {resolved_method}",
                ),
            )
        )

    return results


def main() -> int:
    root = Path.cwd().resolve()
    resolved_method = read_resolved_hook(root)

    if resolved_method != "submit":
        print(
            "[WARN] IX-A4.3C resolved an unexpected Director hook:",
            resolved_method,
        )

    repairs = [
        repair_gap_tracer(root, resolved_method),
        *repair_production_calls(root, resolved_method),
    ]

    report = {
        "schema_version": "genesis_ix_a4_4_v1",
        "resolved_director_method": resolved_method,
        "repairs": [item.to_dict() for item in repairs],
        "production_repairs": sum(
            item.replacements
            for item in repairs[1:]
        ),
        "diagnostic_repairs": repairs[0].replacements,
    }

    output = root / "docs/audits/genesis_ix_a4_4"
    output.mkdir(parents=True, exist_ok=True)

    (output / "runtime_integration_repair.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    lines = [
        "# Genesis IX-A4.4 — Runtime Retrieval Integration Repair",
        "",
        f"**Resolved Director method:** `{resolved_method}`",
        f"**Production replacements:** {report['production_repairs']}",
        f"**Diagnostic replacements:** {report['diagnostic_repairs']}",
        "",
        "| File | Status | Replacements | Details |",
        "|---|---|---:|---|",
    ]

    for item in report["repairs"]:
        lines.append(
            f"| `{item['path']}` | {item['status']} | "
            f"{item['replacements']} | "
            f"{'<br>'.join(item['details'])} |"
        )

    (output / "runtime_integration_repair.md").write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )

    print("=" * 76)
    print("GENESIS IX-A4.4 — RUNTIME RETRIEVAL INTEGRATION REPAIR")
    print("=" * 76)
    print("Resolved Director method :", resolved_method)
    print("Production replacements  :", report["production_repairs"])
    print("Diagnostic replacements  :", report["diagnostic_repairs"])
    print("Report                   :", output)
    print("=" * 76)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
