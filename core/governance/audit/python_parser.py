from __future__ import annotations

import ast
from pathlib import Path
from typing import Iterable

from .models import (
    DiagnosticSeverity,
    ParseDiagnostic,
    PythonImport,
    PythonModule,
    PythonSymbol,
    PythonSymbolKind,
    RepositoryFile,
)


class AstPythonParser:
    def parse(self, root: Path, file: RepositoryFile) -> PythonModule:
        source_path = root / file.path
        diagnostics: list[ParseDiagnostic] = []
        try:
            source = source_path.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            source = source_path.read_text(encoding="utf-8", errors="replace")
            diagnostics.append(ParseDiagnostic(file.path, "python", "Invalid UTF-8 replaced during parsing", DiagnosticSeverity.WARNING, type(exc).__name__))

        try:
            tree = ast.parse(source, filename=file.path, type_comments=True)
        except SyntaxError as exc:
            diagnostics.append(ParseDiagnostic(file.path, "python", exc.msg, DiagnosticSeverity.ERROR, type(exc).__name__, exc.lineno, exc.offset))
            return PythonModule(
                repository_id=file.repository_id,
                path=file.path,
                module_name=module_name_from_path(file.path),
                package_name=package_name_from_path(file.path),
                docstring=None,
                diagnostics=tuple(diagnostics),
            )

        imports = tuple(sorted(_collect_imports(tree), key=lambda item: (item.line or 0, item.module, item.names)))
        symbols = tuple(sorted(_collect_symbols(tree), key=lambda item: (item.line, item.qualified_name, item.kind.value)))
        declared_all = tuple(_extract_declared_all(tree))
        inferred = tuple(sorted(symbol.name for symbol in symbols if symbol.is_public))
        return PythonModule(
            repository_id=file.repository_id,
            path=file.path,
            module_name=module_name_from_path(file.path),
            package_name=package_name_from_path(file.path),
            docstring=ast.get_docstring(tree, clean=False),
            imports=imports,
            symbols=symbols,
            declared_all=declared_all,
            inferred_public_exports=declared_all or inferred,
            diagnostics=tuple(diagnostics),
        )


def module_name_from_path(path: str) -> str:
    parts = list(Path(path).with_suffix("").parts)
    if parts and parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


def package_name_from_path(path: str) -> str | None:
    module = module_name_from_path(path)
    if "." not in module:
        return None
    return module.rsplit(".", 1)[0]


def _collect_imports(tree: ast.AST) -> Iterable[PythonImport]:
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            yield PythonImport(module="", names=tuple(alias.name for alias in node.names), line=node.lineno)
        elif isinstance(node, ast.ImportFrom):
            yield PythonImport(module=node.module or "", names=tuple(alias.name for alias in node.names), level=node.level, line=node.lineno)


def _collect_symbols(tree: ast.Module) -> Iterable[PythonSymbol]:
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            yield _class_symbol(node)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            yield _function_symbol(node)
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            yield from _variable_symbols(node)


def _class_symbol(node: ast.ClassDef) -> PythonSymbol:
    decorators = tuple(_expr_name(item) for item in node.decorator_list)
    bases = tuple(_expr_name(item) for item in node.bases)
    lowered_bases = {base.lower() for base in bases}
    return PythonSymbol(
        name=node.name,
        qualified_name=node.name,
        kind=PythonSymbolKind.CLASS,
        line=node.lineno,
        end_line=getattr(node, "end_lineno", None),
        decorators=decorators,
        bases=bases,
        is_public=not node.name.startswith("_"),
        is_dataclass=any(name.endswith("dataclass") for name in decorators),
        is_enum=any(name.endswith(("Enum", "IntEnum", "StrEnum")) for name in bases),
        is_protocol=any(name.endswith("Protocol") for name in bases),
        is_exception=any(name.endswith(("Exception", "Error")) for name in bases),
        docstring=ast.get_docstring(node, clean=False),
    )


def _function_symbol(node: ast.FunctionDef | ast.AsyncFunctionDef) -> PythonSymbol:
    return PythonSymbol(
        name=node.name,
        qualified_name=node.name,
        kind=PythonSymbolKind.ASYNC_FUNCTION if isinstance(node, ast.AsyncFunctionDef) else PythonSymbolKind.FUNCTION,
        line=node.lineno,
        end_line=getattr(node, "end_lineno", None),
        decorators=tuple(_expr_name(item) for item in node.decorator_list),
        is_public=not node.name.startswith("_"),
        docstring=ast.get_docstring(node, clean=False),
    )


def _variable_symbols(node: ast.Assign | ast.AnnAssign) -> Iterable[PythonSymbol]:
    targets = node.targets if isinstance(node, ast.Assign) else [node.target]
    for target in targets:
        for name in _assigned_names(target):
            if name == "__all__":
                continue
            yield PythonSymbol(name, name, PythonSymbolKind.VARIABLE, node.lineno, getattr(node, "end_lineno", None), is_public=not name.startswith("_"))


def _assigned_names(node: ast.AST) -> Iterable[str]:
    if isinstance(node, ast.Name):
        yield node.id
    elif isinstance(node, (ast.Tuple, ast.List)):
        for item in node.elts:
            yield from _assigned_names(item)


def _extract_declared_all(tree: ast.Module) -> list[str]:
    exports: list[str] = []
    for node in tree.body:
        value: ast.AST | None = None
        if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == "__all__" for target in node.targets):
            value = node.value
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.target.id == "__all__":
            value = node.value
        if isinstance(value, (ast.List, ast.Tuple, ast.Set)):
            for item in value.elts:
                if isinstance(item, ast.Constant) and isinstance(item.value, str):
                    exports.append(item.value)
    return sorted(dict.fromkeys(exports))


def _expr_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        prefix = _expr_name(node.value)
        return f"{prefix}.{node.attr}" if prefix else node.attr
    if isinstance(node, ast.Call):
        return _expr_name(node.func)
    if isinstance(node, ast.Subscript):
        return _expr_name(node.value)
    try:
        return ast.unparse(node)
    except Exception:
        return type(node).__name__
