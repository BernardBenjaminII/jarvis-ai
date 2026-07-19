#!/usr/bin/env bash

set -euo pipefail

PROJECT_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$PROJECT_ROOT"

echo
echo "======================================================================"
echo "JARVIS GEN 2 — GENESIS I-A3"
echo "KNOWLEDGE INTEGRATION AUDIT"
echo "======================================================================"
echo

mkdir -p dev/tools
mkdir -p docs/architecture/convergence

cat > dev/tools/audit_reasoning_knowledge_integration.py <<'PYEOF'
#!/usr/bin/env python3
"""Audit the JARVIS knowledge-to-reasoning integration boundary.

This audit examines:

* core/reasoning/knowledge.py
* core/reasoning/pipeline.py

It records how external knowledge is adapted into canonical EvidenceItem
contracts and how the KnowledgeReasoningPipeline coordinates adaptation,
hypothesis generation, and deterministic reasoning.

The audit never modifies production code.
"""

from __future__ import annotations

import argparse
import ast
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final


PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parents[2]

KNOWLEDGE_SOURCE: Final[Path] = (
    PROJECT_ROOT / "core/reasoning/knowledge.py"
)
PIPELINE_SOURCE: Final[Path] = (
    PROJECT_ROOT / "core/reasoning/pipeline.py"
)

JSON_REPORT_PATH: Final[Path] = (
    PROJECT_ROOT
    / "docs/architecture/convergence/"
    "genesis_1a3_knowledge_integration_audit.json"
)
MARKDOWN_REPORT_PATH: Final[Path] = (
    PROJECT_ROOT
    / "docs/architecture/convergence/"
    "genesis_1a3_knowledge_integration_audit.md"
)

EXPECTED_KNOWLEDGE_CLASSES: Final[tuple[str, ...]] = (
    "KnowledgeEvidenceAdapterError",
    "AdaptedEvidenceBatch",
    "KnowledgeEvidenceAdapter",
)

EXPECTED_PIPELINE_CLASSES: Final[tuple[str, ...]] = (
    "KnowledgeReasoningOutcome",
    "KnowledgeReasoningPipeline",
)


@dataclass(frozen=True, slots=True)
class ParameterRecord:
    """One function or method parameter."""

    name: str
    annotation: str
    has_default: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "annotation": self.annotation,
            "has_default": self.has_default,
        }


@dataclass(frozen=True, slots=True)
class CallableRecord:
    """One function or method discovered by the audit."""

    name: str
    visibility: str
    parameters: tuple[ParameterRecord, ...]
    return_annotation: str
    decorators: tuple[str, ...]
    docstring: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "visibility": self.visibility,
            "parameters": [
                parameter.to_dict()
                for parameter in self.parameters
            ],
            "return_annotation": self.return_annotation,
            "decorators": list(self.decorators),
            "docstring": self.docstring,
        }


@dataclass(frozen=True, slots=True)
class ClassRecord:
    """One class discovered in an integration module."""

    name: str
    bases: tuple[str, ...]
    decorators: tuple[str, ...]
    docstring: str
    fields: tuple[str, ...]
    methods: tuple[CallableRecord, ...]
    is_dataclass: bool
    frozen: bool
    slots: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "bases": list(self.bases),
            "decorators": list(self.decorators),
            "docstring": self.docstring,
            "fields": list(self.fields),
            "methods": [
                method.to_dict()
                for method in self.methods
            ],
            "is_dataclass": self.is_dataclass,
            "frozen": self.frozen,
            "slots": self.slots,
        }


@dataclass(frozen=True, slots=True)
class ModuleRecord:
    """Structural inventory for one Python module."""

    path: str
    docstring: str
    imports: tuple[str, ...]
    functions: tuple[CallableRecord, ...]
    classes: tuple[ClassRecord, ...]
    line_count: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "docstring": self.docstring,
            "imports": list(self.imports),
            "functions": [
                function.to_dict()
                for function in self.functions
            ],
            "classes": [
                class_record.to_dict()
                for class_record in self.classes
            ],
            "line_count": self.line_count,
        }


def _unparse(node: ast.AST | None) -> str:
    """Return a stable source representation for an AST node."""

    if node is None:
        return ""

    return ast.unparse(node)


def _decorator_name(decorator: ast.expr) -> str:
    """Return the readable name of a decorator."""

    if isinstance(decorator, ast.Name):
        return decorator.id

    if isinstance(decorator, ast.Attribute):
        parent = _decorator_name(decorator.value)
        return (
            f"{parent}.{decorator.attr}"
            if parent
            else decorator.attr
        )

    if isinstance(decorator, ast.Call):
        return _decorator_name(decorator.func)

    return _unparse(decorator)


def _visibility(name: str) -> str:
    """Classify a callable by Python naming convention."""

    if name.startswith("__") and name.endswith("__"):
        return "dunder"

    if name.startswith("_"):
        return "private"

    return "public"


def _callable_parameters(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
) -> tuple[ParameterRecord, ...]:
    """Extract function parameters in declaration order."""

    positional = [
        *node.args.posonlyargs,
        *node.args.args,
    ]

    positional_defaults: dict[str, bool] = {}
    default_offset = len(positional) - len(node.args.defaults)

    for index, argument in enumerate(positional):
        positional_defaults[argument.arg] = index >= default_offset

    records: list[ParameterRecord] = []

    for argument in positional:
        records.append(
            ParameterRecord(
                name=argument.arg,
                annotation=_unparse(argument.annotation),
                has_default=positional_defaults[argument.arg],
            )
        )

    if node.args.vararg is not None:
        records.append(
            ParameterRecord(
                name=f"*{node.args.vararg.arg}",
                annotation=_unparse(node.args.vararg.annotation),
                has_default=False,
            )
        )

    for argument, default in zip(
        node.args.kwonlyargs,
        node.args.kw_defaults,
        strict=True,
    ):
        records.append(
            ParameterRecord(
                name=argument.arg,
                annotation=_unparse(argument.annotation),
                has_default=default is not None,
            )
        )

    if node.args.kwarg is not None:
        records.append(
            ParameterRecord(
                name=f"**{node.args.kwarg.arg}",
                annotation=_unparse(node.args.kwarg.annotation),
                has_default=False,
            )
        )

    return tuple(records)


def _callable_record(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
) -> CallableRecord:
    """Build a callable audit record."""

    return CallableRecord(
        name=node.name,
        visibility=_visibility(node.name),
        parameters=_callable_parameters(node),
        return_annotation=_unparse(node.returns),
        decorators=tuple(
            _decorator_name(decorator)
            for decorator in node.decorator_list
        ),
        docstring=ast.get_docstring(node) or "",
    )


def _dataclass_configuration(
    node: ast.ClassDef,
) -> tuple[bool, bool, bool]:
    """Return dataclass, frozen, and slots configuration."""

    for decorator in node.decorator_list:
        if isinstance(decorator, ast.Call):
            if _decorator_name(decorator.func) != "dataclass":
                continue

            keywords = {
                keyword.arg: keyword.value
                for keyword in decorator.keywords
                if keyword.arg is not None
            }

            frozen = (
                isinstance(keywords.get("frozen"), ast.Constant)
                and keywords["frozen"].value is True
            )
            slots = (
                isinstance(keywords.get("slots"), ast.Constant)
                and keywords["slots"].value is True
            )

            return True, frozen, slots

        if _decorator_name(decorator) == "dataclass":
            return True, False, False

    return False, False, False


def _class_record(node: ast.ClassDef) -> ClassRecord:
    """Build a structural record for one class."""

    is_dataclass, frozen, slots = _dataclass_configuration(node)

    fields = tuple(
        statement.target.id
        for statement in node.body
        if isinstance(statement, ast.AnnAssign)
        and isinstance(statement.target, ast.Name)
    )

    methods = tuple(
        _callable_record(statement)
        for statement in node.body
        if isinstance(
            statement,
            (ast.FunctionDef, ast.AsyncFunctionDef),
        )
    )

    return ClassRecord(
        name=node.name,
        bases=tuple(_unparse(base) for base in node.bases),
        decorators=tuple(
            _decorator_name(decorator)
            for decorator in node.decorator_list
        ),
        docstring=ast.get_docstring(node) or "",
        fields=fields,
        methods=methods,
        is_dataclass=is_dataclass,
        frozen=frozen,
        slots=slots,
    )


def _import_record(statement: ast.Import | ast.ImportFrom) -> tuple[str, ...]:
    """Return normalized import records."""

    if isinstance(statement, ast.Import):
        return tuple(
            alias.name
            for alias in statement.names
        )

    module = statement.module or ""
    prefix = "." * statement.level

    return tuple(
        f"{prefix}{module}.{alias.name}".rstrip(".")
        for alias in statement.names
    )


def inspect_module(path: Path) -> ModuleRecord:
    """Parse and inventory one integration module."""

    if not path.is_file():
        raise FileNotFoundError(f"Missing source module: {path}")

    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path))

    imports: list[str] = []

    for statement in tree.body:
        if isinstance(statement, (ast.Import, ast.ImportFrom)):
            imports.extend(_import_record(statement))

    functions = tuple(
        _callable_record(statement)
        for statement in tree.body
        if isinstance(
            statement,
            (ast.FunctionDef, ast.AsyncFunctionDef),
        )
    )

    classes = tuple(
        _class_record(statement)
        for statement in tree.body
        if isinstance(statement, ast.ClassDef)
    )

    return ModuleRecord(
        path=str(path.relative_to(PROJECT_ROOT)),
        docstring=ast.get_docstring(tree) or "",
        imports=tuple(sorted(imports)),
        functions=functions,
        classes=classes,
        line_count=len(source.splitlines()),
    )


def _class_names(module: ModuleRecord) -> tuple[str, ...]:
    return tuple(
        class_record.name
        for class_record in module.classes
    )


def _public_methods(
    module: ModuleRecord,
    class_name: str,
) -> tuple[str, ...]:
    for class_record in module.classes:
        if class_record.name != class_name:
            continue

        return tuple(
            method.name
            for method in class_record.methods
            if method.visibility == "public"
        )

    return ()


def _private_methods(
    module: ModuleRecord,
    class_name: str,
) -> tuple[str, ...]:
    for class_record in module.classes:
        if class_record.name != class_name:
            continue

        return tuple(
            method.name
            for method in class_record.methods
            if method.visibility == "private"
        )

    return ()


def build_report() -> dict[str, Any]:
    """Build the deterministic knowledge-integration audit."""

    knowledge = inspect_module(KNOWLEDGE_SOURCE)
    pipeline = inspect_module(PIPELINE_SOURCE)

    knowledge_class_names = _class_names(knowledge)
    pipeline_class_names = _class_names(pipeline)

    missing_knowledge_classes = sorted(
        set(EXPECTED_KNOWLEDGE_CLASSES)
        - set(knowledge_class_names)
    )
    missing_pipeline_classes = sorted(
        set(EXPECTED_PIPELINE_CLASSES)
        - set(pipeline_class_names)
    )

    adapter_public_methods = _public_methods(
        knowledge,
        "KnowledgeEvidenceAdapter",
    )
    adapter_private_methods = _private_methods(
        knowledge,
        "KnowledgeEvidenceAdapter",
    )
    pipeline_public_methods = _public_methods(
        pipeline,
        "KnowledgeReasoningPipeline",
    )
    pipeline_private_methods = _private_methods(
        pipeline,
        "KnowledgeReasoningPipeline",
    )

    all_imports = {
        *knowledge.imports,
        *pipeline.imports,
    }

    conclusions = {
        "knowledge_adapter_present": (
            "KnowledgeEvidenceAdapter"
            in knowledge_class_names
        ),
        "adapted_batch_contract_present": (
            "AdaptedEvidenceBatch"
            in knowledge_class_names
        ),
        "knowledge_pipeline_present": (
            "KnowledgeReasoningPipeline"
            in pipeline_class_names
        ),
        "pipeline_outcome_contract_present": (
            "KnowledgeReasoningOutcome"
            in pipeline_class_names
        ),
        "canonical_evidence_dependency_present": any(
            import_name.endswith(".EvidenceItem")
            for import_name in all_imports
        ),
        "canonical_reasoning_request_dependency_present": any(
            import_name.endswith(".ReasoningRequest")
            for import_name in all_imports
        ),
        "canonical_reasoning_result_dependency_present": any(
            import_name.endswith(".ReasoningResult")
            for import_name in all_imports
        ),
        "reasoning_engine_dependency_present": any(
            import_name.endswith(".ReasoningEngine")
            for import_name in all_imports
        ),
        "hypothesis_generator_dependency_present": any(
            import_name.endswith(
                ".DeterministicHypothesisGenerator"
            )
            for import_name in all_imports
        ),
        "expected_knowledge_classes_present": (
            not missing_knowledge_classes
        ),
        "expected_pipeline_classes_present": (
            not missing_pipeline_classes
        ),
    }

    integration_flow = (
        "External knowledge or ranked retrieval results",
        "KnowledgeEvidenceAdapter",
        "AdaptedEvidenceBatch",
        "Canonical EvidenceItem contracts",
        "DeterministicHypothesisGenerator",
        "ReasoningRequest",
        "ReasoningEngine",
        "ReasoningResult",
        "KnowledgeReasoningOutcome",
    )

    architectural_findings = (
        "Knowledge adaptation is already separated from core inference and "
        "reasoning orchestration.",
        "The adapter is the canonical anti-corruption boundary between "
        "retrieval-shaped data and immutable reasoning evidence.",
        "The pipeline coordinates existing subsystems instead of duplicating "
        "their internal responsibilities.",
        "The pipeline should remain a composition layer and must not become "
        "the owner of evidence scoring, inference, or executive policy.",
        "Future ReasoningSession support should wrap or contextualize this "
        "pipeline rather than replace the adapter and engine boundaries.",
        "Evidence provenance evolution should begin at the adapter boundary "
        "because that is where external source metadata becomes canonical "
        "reasoning evidence.",
    )

    migration_constraints = (
        "Preserve KnowledgeEvidenceAdapter as the single conversion boundary "
        "for retrieval results entering reasoning.",
        "Preserve EvidenceItem as the canonical evidence contract until an "
        "explicit compatible migration is approved.",
        "Preserve deterministic identifiers generated from stable source "
        "content and references.",
        "Do not allow the integration pipeline to retrieve knowledge directly "
        "unless retrieval is explicitly delegated through an injected "
        "dependency.",
        "Do not introduce executive governance into the adapter; governance "
        "belongs to a future ReasoningSession or Executive integration layer.",
        "Do not permit pipeline orchestration to mutate knowledge, evidence, "
        "hypotheses, or reasoning results.",
    )

    return {
        "audit_id": "GENESIS-I-A3",
        "title": "Knowledge Integration Audit",
        "sources": [
            knowledge.path,
            pipeline.path,
        ],
        "modules": {
            "knowledge": knowledge.to_dict(),
            "pipeline": pipeline.to_dict(),
        },
        "expected_classes": {
            "knowledge": list(EXPECTED_KNOWLEDGE_CLASSES),
            "pipeline": list(EXPECTED_PIPELINE_CLASSES),
        },
        "missing_expected_classes": {
            "knowledge": missing_knowledge_classes,
            "pipeline": missing_pipeline_classes,
        },
        "public_interfaces": {
            "KnowledgeEvidenceAdapter": list(
                adapter_public_methods
            ),
            "KnowledgeReasoningPipeline": list(
                pipeline_public_methods
            ),
        },
        "private_helpers": {
            "KnowledgeEvidenceAdapter": list(
                adapter_private_methods
            ),
            "KnowledgeReasoningPipeline": list(
                pipeline_private_methods
            ),
        },
        "integration_flow": list(integration_flow),
        "conclusions": conclusions,
        "architectural_findings": list(
            architectural_findings
        ),
        "migration_constraints": list(
            migration_constraints
        ),
    }


def render_json(report: dict[str, Any]) -> str:
    """Render the canonical JSON audit report."""

    return json.dumps(
        report,
        indent=2,
        sort_keys=True,
        ensure_ascii=True,
    ) + "\n"


def _yes_no(value: bool) -> str:
    return "Yes" if value else "No"


def render_markdown(report: dict[str, Any]) -> str:
    """Render the human-readable audit report."""

    knowledge = report["modules"]["knowledge"]
    pipeline = report["modules"]["pipeline"]

    lines: list[str] = [
        "# Genesis I-A3 — Knowledge Integration Audit",
        "",
        "**Status:** Architecture baseline  ",
        "**Production code modified:** No  ",
        "**Audited modules:**",
        "",
        "- `core/reasoning/knowledge.py`",
        "- `core/reasoning/pipeline.py`",
        "",
        "## Purpose",
        "",
        "This audit records the existing boundary between retrieved knowledge "
        "and deterministic reasoning. It establishes the baseline that future "
        "Reasoning Session and evidence-provenance work must preserve.",
        "",
        "## Executive Finding",
        "",
        "JARVIS already has a distinct knowledge-adaptation boundary and a "
        "composition pipeline. Genesis should preserve both. Future changes "
        "should add session context and richer provenance around these "
        "components rather than moving their responsibilities into a new "
        "parallel architecture.",
        "",
        "## Integration Flow",
        "",
        "```text",
    ]

    for index, stage in enumerate(report["integration_flow"]):
        lines.append(stage)

        if index < len(report["integration_flow"]) - 1:
            lines.append("        ↓")

    lines.extend(
        [
            "```",
            "",
            "## Module Inventory",
            "",
            "| Module | Lines | Classes | Top-level functions |",
            "|---|---:|---:|---:|",
            (
                f"| `{knowledge['path']}` | "
                f"{knowledge['line_count']} | "
                f"{len(knowledge['classes'])} | "
                f"{len(knowledge['functions'])} |"
            ),
            (
                f"| `{pipeline['path']}` | "
                f"{pipeline['line_count']} | "
                f"{len(pipeline['classes'])} | "
                f"{len(pipeline['functions'])} |"
            ),
            "",
            "## Knowledge Adapter",
            "",
        ]
    )

    for class_record in knowledge["classes"]:
        lines.extend(
            [
                f"### `{class_record['name']}`",
                "",
                class_record["docstring"] or "_No class docstring._",
                "",
                f"- Dataclass: {_yes_no(class_record['is_dataclass'])}",
                f"- Frozen: {_yes_no(class_record['frozen'])}",
                f"- Slotted: {_yes_no(class_record['slots'])}",
                "",
            ]
        )

        if class_record["fields"]:
            lines.append("Fields:")
            lines.append("")

            for field_name in class_record["fields"]:
                lines.append(f"- `{field_name}`")

            lines.append("")

        if class_record["methods"]:
            lines.append("Methods:")
            lines.append("")

            for method in class_record["methods"]:
                parameter_names = ", ".join(
                    parameter["name"]
                    for parameter in method["parameters"]
                )
                return_annotation = (
                    f" -> {method['return_annotation']}"
                    if method["return_annotation"]
                    else ""
                )
                lines.append(
                    f"- `{method['name']}({parameter_names})"
                    f"{return_annotation}`"
                )

            lines.append("")

    lines.extend(
        [
            "## Knowledge Reasoning Pipeline",
            "",
        ]
    )

    for class_record in pipeline["classes"]:
        lines.extend(
            [
                f"### `{class_record['name']}`",
                "",
                class_record["docstring"] or "_No class docstring._",
                "",
                f"- Dataclass: {_yes_no(class_record['is_dataclass'])}",
                f"- Frozen: {_yes_no(class_record['frozen'])}",
                f"- Slotted: {_yes_no(class_record['slots'])}",
                "",
            ]
        )

        if class_record["fields"]:
            lines.append("Fields:")
            lines.append("")

            for field_name in class_record["fields"]:
                lines.append(f"- `{field_name}`")

            lines.append("")

        if class_record["methods"]:
            lines.append("Methods:")
            lines.append("")

            for method in class_record["methods"]:
                parameter_names = ", ".join(
                    parameter["name"]
                    for parameter in method["parameters"]
                )
                return_annotation = (
                    f" -> {method['return_annotation']}"
                    if method["return_annotation"]
                    else ""
                )
                lines.append(
                    f"- `{method['name']}({parameter_names})"
                    f"{return_annotation}`"
                )

            lines.append("")

    lines.extend(
        [
            "## Public Integration Interfaces",
            "",
        ]
    )

    for class_name, methods in report["public_interfaces"].items():
        lines.append(f"### `{class_name}`")
        lines.append("")

        if methods:
            for method_name in methods:
                lines.append(f"- `{method_name}()`")
        else:
            lines.append("- No public methods discovered.")

        lines.append("")

    lines.extend(
        [
            "## Structural Conclusions",
            "",
        ]
    )

    for name, value in report["conclusions"].items():
        label = name.replace("_", " ").capitalize()
        lines.append(f"- **{label}:** {_yes_no(value)}")

    lines.extend(
        [
            "",
            "## Architectural Findings",
            "",
        ]
    )

    for finding in report["architectural_findings"]:
        lines.append(f"- {finding}")

    lines.extend(
        [
            "",
            "## Migration Constraints",
            "",
        ]
    )

    for constraint in report["migration_constraints"]:
        lines.append(f"- {constraint}")

    lines.extend(
        [
            "",
            "## Architectural Decision",
            "",
            "`KnowledgeEvidenceAdapter` remains the canonical boundary where "
            "external retrieval data becomes immutable reasoning evidence.",
            "",
            "`KnowledgeReasoningPipeline` remains a composition layer. It may "
            "coordinate adaptation, hypothesis generation, and reasoning, but "
            "it must not absorb the responsibilities of those components.",
            "",
            "The future `ReasoningSession` will provide execution context, "
            "governance, budgets, and lifecycle state around this existing "
            "pipeline.",
            "",
            "## Next Genesis Step",
            "",
            "**Genesis I-A4 — Canonical Reasoning Architecture Baseline**",
            "",
            "I-A4 will consolidate the contract, service, knowledge-adapter, "
            "and pipeline findings into one authoritative architecture map "
            "before the Reasoning Session model is introduced.",
            "",
        ]
    )

    return "\n".join(lines)


def _check_file(path: Path, expected: str) -> bool:
    """Check whether a generated file is present and current."""

    relative = path.relative_to(PROJECT_ROOT)

    if not path.is_file():
        print(f"[FAIL] Missing generated report: {relative}")
        return False

    actual = path.read_text(encoding="utf-8")

    if actual != expected:
        print(f"[FAIL] Stale generated report: {relative}")
        return False

    print(f"[PASS] Current report: {relative}")
    return True


def write_reports(
    json_content: str,
    markdown_content: str,
) -> None:
    """Write deterministic JSON and Markdown reports."""

    JSON_REPORT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    JSON_REPORT_PATH.write_text(
        json_content,
        encoding="utf-8",
    )
    MARKDOWN_REPORT_PATH.write_text(
        markdown_content,
        encoding="utf-8",
    )

    print(
        "[WRITE] "
        f"{JSON_REPORT_PATH.relative_to(PROJECT_ROOT)}"
    )
    print(
        "[WRITE] "
        f"{MARKDOWN_REPORT_PATH.relative_to(PROJECT_ROOT)}"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Audit JARVIS knowledge-to-reasoning integration."
        )
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail when generated reports are missing or stale.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    try:
        report = build_report()
    except (OSError, SyntaxError, ValueError) as exc:
        print(
            "[FAIL] Unable to audit knowledge integration: "
            f"{exc}"
        )
        return 1

    json_content = render_json(report)
    markdown_content = render_markdown(report)

    if args.check:
        json_current = _check_file(
            JSON_REPORT_PATH,
            json_content,
        )
        markdown_current = _check_file(
            MARKDOWN_REPORT_PATH,
            markdown_content,
        )

        return (
            0
            if json_current and markdown_current
            else 1
        )

    write_reports(
        json_content,
        markdown_content,
    )

    knowledge_classes = len(
        report["modules"]["knowledge"]["classes"]
    )
    pipeline_classes = len(
        report["modules"]["pipeline"]["classes"]
    )

    print(
        "[PASS] Audited knowledge integration: "
        f"{knowledge_classes} knowledge classes, "
        f"{pipeline_classes} pipeline classes"
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
PYEOF

cat > dev/verify_genesis_1a3.sh <<'VERIFYEOF'
#!/usr/bin/env bash

set -euo pipefail

PROJECT_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
PYTHON_BIN="${PYTHON_BIN:-python}"

cd "$PROJECT_ROOT"

echo
echo "======================================================================"
echo "JARVIS GEN 2 — GENESIS I-A3"
echo "KNOWLEDGE INTEGRATION AUDIT"
echo "======================================================================"
echo

failures=0

pass() {
    echo "[PASS] $1"
}

fail() {
    echo "[FAIL] $1"
    failures=$((failures + 1))
}

check_file() {
    local path="$1"

    if [ -f "$path" ]; then
        pass "$path"
    else
        fail "$path"
    fi
}

check_file "core/reasoning/knowledge.py"
check_file "core/reasoning/pipeline.py"
check_file \
    "dev/tools/audit_reasoning_knowledge_integration.py"
check_file "dev/verify_genesis_1a3.sh"

if "$PYTHON_BIN" -m py_compile \
    core/reasoning/knowledge.py \
    core/reasoning/pipeline.py \
    dev/tools/audit_reasoning_knowledge_integration.py
then
    pass "Knowledge integration modules compile"
else
    fail "Knowledge integration modules compile"
fi

if "$PYTHON_BIN" \
    dev/tools/audit_reasoning_knowledge_integration.py
then
    pass "Knowledge integration audit generated"
else
    fail "Knowledge integration audit generated"
fi

check_file \
    "docs/architecture/convergence/genesis_1a3_knowledge_integration_audit.json"
check_file \
    "docs/architecture/convergence/genesis_1a3_knowledge_integration_audit.md"

if "$PYTHON_BIN" \
    dev/tools/audit_reasoning_knowledge_integration.py \
    --check
then
    pass "Generated audit reports are deterministic and current"
else
    fail "Generated audit reports are deterministic and current"
fi

if "$PYTHON_BIN" - <<'PY'
from __future__ import annotations

import json
from pathlib import Path

report_path = Path(
    "docs/architecture/convergence/"
    "genesis_1a3_knowledge_integration_audit.json"
)

report = json.loads(
    report_path.read_text(encoding="utf-8")
)

assert report["audit_id"] == "GENESIS-I-A3"

assert report["sources"] == [
    "core/reasoning/knowledge.py",
    "core/reasoning/pipeline.py",
]

knowledge_classes = {
    item["name"]
    for item in report["modules"]["knowledge"]["classes"]
}
pipeline_classes = {
    item["name"]
    for item in report["modules"]["pipeline"]["classes"]
}

assert {
    "KnowledgeEvidenceAdapterError",
    "AdaptedEvidenceBatch",
    "KnowledgeEvidenceAdapter",
}.issubset(knowledge_classes)

assert {
    "KnowledgeReasoningOutcome",
    "KnowledgeReasoningPipeline",
}.issubset(pipeline_classes)

assert (
    report["missing_expected_classes"]["knowledge"]
    == []
)
assert (
    report["missing_expected_classes"]["pipeline"]
    == []
)

assert (
    report["conclusions"]["knowledge_adapter_present"]
    is True
)
assert (
    report["conclusions"]["adapted_batch_contract_present"]
    is True
)
assert (
    report["conclusions"]["knowledge_pipeline_present"]
    is True
)
assert (
    report["conclusions"]["pipeline_outcome_contract_present"]
    is True
)
assert (
    report["conclusions"][
        "expected_knowledge_classes_present"
    ]
    is True
)
assert (
    report["conclusions"][
        "expected_pipeline_classes_present"
    ]
    is True
)

assert len(report["integration_flow"]) >= 7
assert report["architectural_findings"]
assert report["migration_constraints"]

print("[PASS] Canonical knowledge-integration assertions")
PY
then
    pass "Canonical knowledge-integration structure"
else
    fail "Canonical knowledge-integration structure"
fi

if "$PYTHON_BIN" - <<'PY'
from __future__ import annotations

import inspect

from core.reasoning.knowledge import (
    AdaptedEvidenceBatch,
    KnowledgeEvidenceAdapter,
    KnowledgeEvidenceAdapterError,
)
from core.reasoning.pipeline import (
    KnowledgeReasoningOutcome,
    KnowledgeReasoningPipeline,
)

assert inspect.isclass(KnowledgeEvidenceAdapterError)
assert inspect.isclass(AdaptedEvidenceBatch)
assert inspect.isclass(KnowledgeEvidenceAdapter)
assert inspect.isclass(KnowledgeReasoningOutcome)
assert inspect.isclass(KnowledgeReasoningPipeline)

adapter_methods = {
    name
    for name, value in inspect.getmembers(
        KnowledgeEvidenceAdapter,
        predicate=inspect.isfunction,
    )
    if not name.startswith("__")
}

pipeline_methods = {
    name
    for name, value in inspect.getmembers(
        KnowledgeReasoningPipeline,
        predicate=inspect.isfunction,
    )
    if not name.startswith("__")
}

assert adapter_methods
assert pipeline_methods

print(
    "[PASS] Knowledge adapter importability: "
    + ", ".join(sorted(adapter_methods))
)
print(
    "[PASS] Knowledge pipeline importability: "
    + ", ".join(sorted(pipeline_methods))
)
PY
then
    pass "Knowledge integration import smoke test"
else
    fail "Knowledge integration import smoke test"
fi

if "$PYTHON_BIN" - <<'PY'
from __future__ import annotations

import ast
from pathlib import Path

for relative_path in (
    "core/reasoning/knowledge.py",
    "core/reasoning/pipeline.py",
):
    source_path = Path(relative_path)
    tree = ast.parse(
        source_path.read_text(encoding="utf-8"),
        filename=str(source_path),
    )

    forbidden_calls = {
        "requests.get",
        "requests.post",
        "subprocess.run",
        "subprocess.Popen",
        "os.system",
    }

    discovered: set[str] = set()

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue

        if isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name):
                discovered.add(
                    f"{node.func.value.id}.{node.func.attr}"
                )

    violations = sorted(
        forbidden_calls.intersection(discovered)
    )

    assert not violations, (
        f"{relative_path} contains prohibited direct external "
        f"operations: {violations}"
    )

print(
    "[PASS] Knowledge integration remains free of direct "
    "network and process execution"
)
PY
then
    pass "Knowledge integration boundary isolation"
else
    fail "Knowledge integration boundary isolation"
fi

echo
echo "----------------------------------------------------------------------"
echo "Checks failed : ${failures}"

if [ "$failures" -eq 0 ]; then
    echo "Overall status: EXCELLENT"
    echo "======================================================================"
    exit 0
fi

echo "Overall status: ATTENTION REQUIRED"
echo "======================================================================"
exit 1
VERIFYEOF

chmod +x \
    dev/tools/audit_reasoning_knowledge_integration.py
chmod +x dev/verify_genesis_1a3.sh

echo "[CREATE] dev/tools/audit_reasoning_knowledge_integration.py"
echo "[CREATE] dev/verify_genesis_1a3.sh"

echo
echo "[PASS] Genesis I-A3 audit tooling installed"
echo
