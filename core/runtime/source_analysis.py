from __future__ import annotations

import ast
import inspect
import textwrap
from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class CallableSource:
    status: str
    source: str | None
    source_file: str | None
    source_line: int | None
    signature: str | None
    qualname: str | None
    module: str | None
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ParsedCallable:
    status: str
    source: CallableSource
    tree: ast.AST | None
    calls: tuple[dict[str, Any], ...]
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "source": self.source.to_dict(),
            "calls": list(self.calls),
            "error": self.error,
        }


def callable_signature(value: Any) -> str | None:
    try:
        return str(inspect.signature(value))
    except Exception:
        return None


def callable_location(value: Any) -> tuple[str | None, int | None]:
    try:
        source_file = inspect.getsourcefile(value)
    except Exception:
        source_file = None

    try:
        source_line = inspect.getsourcelines(value)[1]
    except Exception:
        source_line = None

    return source_file, source_line


def unwrap_callable(value: Any) -> Any:
    try:
        return inspect.unwrap(value)
    except Exception:
        return value


def normalized_source(value: Any) -> CallableSource:
    target = unwrap_callable(value)
    source_file, source_line = callable_location(target)

    try:
        source = textwrap.dedent(inspect.getsource(target))
        return CallableSource(
            status="available",
            source=source,
            source_file=source_file,
            source_line=source_line,
            signature=callable_signature(value),
            qualname=getattr(value, "__qualname__", None),
            module=getattr(value, "__module__", None),
        )
    except Exception as exc:
        return CallableSource(
            status="unavailable",
            source=None,
            source_file=source_file,
            source_line=source_line,
            signature=callable_signature(value),
            qualname=getattr(value, "__qualname__", None),
            module=getattr(value, "__module__", None),
            error=f"{type(exc).__name__}: {exc}",
        )


def parse_source_text(source: str, filename: str = "<unknown>"):
    try:
        return ast.parse(textwrap.dedent(source), filename=filename), None
    except SyntaxError as exc:
        return None, f"{type(exc).__name__}: {exc}"


def callable_ast(value: Any) -> ParsedCallable:
    source = normalized_source(value)

    if source.source is None:
        return ParsedCallable(
            status="source_unavailable",
            source=source,
            tree=None,
            calls=(),
            error=source.error,
        )

    tree, error = parse_source_text(
        source.source,
        source.source_file or "<unknown>",
    )

    if tree is None:
        return ParsedCallable(
            status="source_unparseable",
            source=source,
            tree=None,
            calls=(),
            error=error,
        )

    calls = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        try:
            target = ast.unparse(node.func)
        except Exception:
            target = "<unknown>"
        calls.append(
            {
                "target": target,
                "relative_line": getattr(node, "lineno", None),
                "absolute_line": (
                    source.source_line + node.lineno - 1
                    if source.source_line is not None
                    and getattr(node, "lineno", None) is not None
                    else None
                ),
            }
        )

    return ParsedCallable(
        status="parsed",
        source=source,
        tree=tree,
        calls=tuple(calls),
    )


def callable_fallback(value: Any) -> dict[str, Any]:
    target = unwrap_callable(value)
    try:
        members = [
            name
            for name, member in inspect.getmembers(target)
            if callable(member)
        ]
    except Exception:
        members = []

    try:
        closure = inspect.getclosurevars(target)
        closure_data = {
            "nonlocals": sorted(closure.nonlocals),
            "globals": sorted(closure.globals),
            "builtins": sorted(closure.builtins),
            "unbound": sorted(closure.unbound),
        }
    except Exception:
        closure_data = {}

    source_file, source_line = callable_location(target)
    return {
        "signature": callable_signature(value),
        "module": getattr(value, "__module__", None),
        "qualname": getattr(value, "__qualname__", None),
        "source_file": source_file,
        "source_line": source_line,
        "callable_members": members,
        "closure": closure_data,
    }
