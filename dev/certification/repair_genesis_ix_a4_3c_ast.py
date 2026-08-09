from __future__ import annotations

from pathlib import Path


IMPORT = "from core.runtime.source_analysis import callable_ast\n"


def repair(path: Path) -> bool:
    source = path.read_text(encoding="utf-8")

    if IMPORT.strip() not in source:
        anchor = "from typing import Any, Callable, Mapping\n"
        if anchor not in source:
            raise RuntimeError("Expected typing import anchor is absent.")
        source = source.replace(anchor, anchor + "\n" + IMPORT, 1)

    old = '''        try:
            source = inspect.getsource(entry)
            source_file = inspect.getsourcefile(entry)
            start_line = inspect.getsourcelines(entry)[1]
        except Exception as exc:
            return {
                "status": "source_unavailable",
                "entry_method": "execute",
                "error": f"{type(exc).__name__}: {exc}",
                "calls": [],
            }

        tree = ast.parse(source)
        calls: list[dict[str, Any]] = []

        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            try:
                target = ast.unparse(node.func)
            except Exception:
                target = "<unknown>"

            if any(
                token in target
                for token in (
                    "ground",
                    "assess",
                    "director",
                    "synthesis",
                    "compile",
                    "observe",
                )
            ):
                calls.append(
                    {
                        "target": target,
                        "relative_line": getattr(node, "lineno", None),
                        "absolute_line": (
                            start_line + node.lineno - 1
                            if getattr(node, "lineno", None)
                            else None
                        ),
                    }
                )
'''

    new = '''        parsed = callable_ast(entry)

        if parsed.status != "parsed":
            return {
                "status": parsed.status,
                "entry_method": "execute",
                "source_file": parsed.source.source_file,
                "source_line": parsed.source.source_line,
                "error": parsed.error,
                "fallback": {
                    "signature": parsed.source.signature,
                    "qualname": parsed.source.qualname,
                    "module": parsed.source.module,
                },
                "calls": [],
            }

        source_file = parsed.source.source_file
        start_line = parsed.source.source_line
        calls: list[dict[str, Any]] = []

        for call in parsed.calls:
            target = str(call.get("target") or "<unknown>")

            if any(
                token in target
                for token in (
                    "ground",
                    "assess",
                    "director",
                    "synthesis",
                    "compile",
                    "observe",
                )
            ):
                calls.append(dict(call))
'''

    if old in source:
        source = source.replace(old, new, 1)
        path.write_text(source, encoding="utf-8")
        return True

    if "parsed = callable_ast(entry)" in source:
        return False

    raise RuntimeError(
        "Expected IX-A4.3C AST parsing block was not found."
    )


def main() -> int:
    target = (
        Path.cwd()
        / "core/retrieval/call_graph/reconstructor.py"
    )
    changed = repair(target)
    print(
        "[PASS] IX-A4.3C AST reconstruction repaired."
        if changed
        else "[PASS] IX-A4.3C AST repair already present."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
