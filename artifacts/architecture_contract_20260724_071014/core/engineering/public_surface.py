"""Deterministic, non-executing evaluation of Python public API surfaces."""

from __future__ import annotations

import ast
from dataclasses import dataclass
from typing import Callable, Mapping


ImportedAllResolver = Callable[[str], tuple[str, ...] | None]


@dataclass(frozen=True, slots=True)
class PublicSurfaceResult:
    """Result of statically evaluating a module's ``__all__`` contract."""

    symbols: tuple[str, ...]
    resolved: bool
    findings: tuple[str, ...] = ()


class StaticPublicSurfaceEvaluator:
    """Evaluate supported ``__all__`` construction patterns using AST only.

    The evaluator deliberately supports a constrained, deterministic subset of
    Python expressions. It never imports or executes repository code.
    """

    def __init__(
        self,
        *,
        module_name: str,
        is_package: bool,
        imported_all_resolver: ImportedAllResolver | None = None,
    ) -> None:
        self._module_name = module_name
        self._is_package = is_package
        self._resolver = imported_all_resolver
        self._environment: dict[str, tuple[str, ...]] = {}
        self._findings: list[str] = []

    def evaluate(self, tree: ast.Module) -> PublicSurfaceResult:
        """Evaluate statements in source order and return the final surface."""

        self._evaluate_statements(tree.body)
        symbols = self._environment.get("__all__")
        if symbols is None:
            return PublicSurfaceResult(
                symbols=(),
                resolved=False,
                findings=tuple(
                    dict.fromkeys(
                        (
                            *self._findings,
                            "No statically resolvable __all__ assignment.",
                        )
                    )
                ),
            )

        return PublicSurfaceResult(
            symbols=self._deduplicate(symbols),
            resolved=True,
            findings=tuple(dict.fromkeys(self._findings)),
        )

    def _evaluate_statements(self, statements: list[ast.stmt]) -> None:
        for statement in statements:
            if isinstance(statement, ast.ImportFrom):
                self._evaluate_import_from(statement)
            elif isinstance(statement, ast.Assign):
                value = self._evaluate_expression(statement.value)
                if value is not None:
                    for target in statement.targets:
                        self._assign(target, value)
            elif isinstance(statement, ast.AnnAssign):
                if statement.value is None:
                    continue
                value = self._evaluate_expression(statement.value)
                if value is not None:
                    self._assign(statement.target, value)
            elif isinstance(statement, ast.AugAssign):
                if not isinstance(statement.op, ast.Add):
                    continue
                if not isinstance(statement.target, ast.Name):
                    continue
                left = self._environment.get(statement.target.id)
                right = self._evaluate_expression(statement.value)
                if left is not None and right is not None:
                    self._environment[statement.target.id] = left + right
            elif isinstance(statement, ast.Try):
                self._evaluate_try(statement)
            elif isinstance(statement, ast.If):
                self._evaluate_if(statement)
            elif isinstance(statement, ast.Delete):
                for target in statement.targets:
                    if isinstance(target, ast.Name):
                        self._environment.pop(target.id, None)

    def _evaluate_try(self, statement: ast.Try) -> None:
        """Prefer the try body when it resolves; otherwise use a handler."""

        original = dict(self._environment)
        self._evaluate_statements(statement.body)

        if self._environment != original:
            self._evaluate_statements(statement.orelse)
            self._evaluate_statements(statement.finalbody)
            return

        self._environment = original
        for handler in statement.handlers:
            candidate = dict(self._environment)
            self._evaluate_statements(handler.body)
            if self._environment != candidate:
                break
        self._evaluate_statements(statement.finalbody)

    def _evaluate_if(self, statement: ast.If) -> None:
        """Evaluate the branch that produces deterministic assignments.

        This is intentionally conservative. It does not attempt to determine
        arbitrary runtime truth values.
        """

        original = dict(self._environment)

        body_environment = dict(original)
        self._environment = body_environment
        self._evaluate_statements(statement.body)
        body_environment = dict(self._environment)

        self._environment = dict(original)
        self._evaluate_statements(statement.orelse)
        else_environment = dict(self._environment)

        if body_environment == else_environment:
            self._environment = body_environment
        else:
            self._environment = original
            self._findings.append(
                "Conditional public-surface assignment could not be resolved "
                "without executing code."
            )

    def _evaluate_import_from(self, statement: ast.ImportFrom) -> None:
        if self._resolver is None:
            return

        imported_module = self._absolute_import_name(
            module=statement.module,
            level=statement.level,
        )
        if not imported_module:
            return

        for alias in statement.names:
            if alias.name != "__all__":
                continue
            resolved = self._resolver(imported_module)
            if resolved is not None:
                self._environment[alias.asname or alias.name] = resolved

    def _assign(self, target: ast.expr, value: tuple[str, ...]) -> None:
        if isinstance(target, ast.Name):
            self._environment[target.id] = value

    def _evaluate_expression(
        self,
        expression: ast.expr,
    ) -> tuple[str, ...] | None:
        if isinstance(expression, ast.Constant):
            if isinstance(expression.value, str):
                return (expression.value,)
            return None

        if isinstance(expression, ast.Name):
            return self._environment.get(expression.id)

        if isinstance(expression, ast.Starred):
            return self._evaluate_expression(expression.value)

        if isinstance(expression, (ast.List, ast.Tuple, ast.Set)):
            values: list[str] = []
            for item in expression.elts:
                evaluated = self._evaluate_expression(item)
                if evaluated is None:
                    return None
                values.extend(evaluated)
            return tuple(values)

        if isinstance(expression, ast.BinOp) and isinstance(expression.op, ast.Add):
            left = self._evaluate_expression(expression.left)
            right = self._evaluate_expression(expression.right)
            if left is None or right is None:
                return None
            return left + right

        if isinstance(expression, ast.Call):
            return self._evaluate_call(expression)

        return None

    def _evaluate_call(self, expression: ast.Call) -> tuple[str, ...] | None:
        if expression.keywords:
            return None

        if isinstance(expression.func, ast.Name):
            if expression.func.id not in {"tuple", "list", "set"}:
                return None
            if not expression.args:
                return ()
            if len(expression.args) != 1:
                return None
            return self._evaluate_expression(expression.args[0])

        if (
            isinstance(expression.func, ast.Attribute)
            and isinstance(expression.func.value, ast.Name)
            and expression.func.value.id == "dict"
            and expression.func.attr == "fromkeys"
        ):
            if not expression.args:
                return ()
            if len(expression.args) > 2:
                return None
            values = self._evaluate_expression(expression.args[0])
            if values is None:
                return None
            return self._deduplicate(values)

        return None

    def _absolute_import_name(
        self,
        *,
        module: str | None,
        level: int,
    ) -> str:
        if level == 0:
            return module or ""

        parts = self._module_name.split(".")
        package_parts = parts if self._is_package else parts[:-1]
        ascend = max(level - 1, 0)

        if ascend > len(package_parts):
            return ""

        base = package_parts[: len(package_parts) - ascend]
        suffix = module.split(".") if module else []
        return ".".join((*base, *suffix))

    @staticmethod
    def _deduplicate(values: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(dict.fromkeys(values))


def evaluate_public_surface(
    tree: ast.Module,
    *,
    module_name: str,
    is_package: bool,
    imported_all_resolver: ImportedAllResolver | None = None,
) -> PublicSurfaceResult:
    """Convenience function for deterministic public-surface evaluation."""

    return StaticPublicSurfaceEvaluator(
        module_name=module_name,
        is_package=is_package,
        imported_all_resolver=imported_all_resolver,
    ).evaluate(tree)


__all__ = [
    "ImportedAllResolver",
    "PublicSurfaceResult",
    "StaticPublicSurfaceEvaluator",
    "evaluate_public_surface",
]
