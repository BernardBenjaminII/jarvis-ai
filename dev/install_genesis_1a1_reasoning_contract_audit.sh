#!/usr/bin/env bash

set -euo pipefail

PROJECT_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$PROJECT_ROOT"

echo
echo "======================================================================"
echo "JARVIS GEN 2 — GENESIS I-A1"
echo "REASONING CONTRACT AUDIT"
echo "======================================================================"
echo

mkdir -p dev/tools
mkdir -p docs/architecture/convergence

cat > dev/tools/audit_reasoning_contracts.py <<'PYEOF'
#!/usr/bin/env python3
"""Audit the canonical Reasoning Engine contract model.

The audit is intentionally read-only with respect to production code. It parses
``core/reasoning/models.py`` and produces deterministic JSON and Markdown
architecture reports.

Usage:
    python dev/tools/audit_reasoning_contracts.py
    python dev/tools/audit_reasoning_contracts.py --check
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
SOURCE_PATH: Final[Path] = PROJECT_ROOT / "core/reasoning/models.py"
JSON_REPORT_PATH: Final[Path] = (
    PROJECT_ROOT
    / "docs/architecture/convergence/"
    "genesis_1a1_reasoning_contract_audit.json"
)
MARKDOWN_REPORT_PATH: Final[Path] = (
    PROJECT_ROOT
    / "docs/architecture/convergence/"
    "genesis_1a1_reasoning_contract_audit.md"
)

EXPECTED_CONTRACTS: Final[tuple[str, ...]] = (
    "EvidenceItem",
    "Hypothesis",
    "ReasoningRequest",
    "HypothesisAssessment",
    "ReasoningTraceStep",
    "PlanningRecommendation",
    "ReasoningResult",
)

EXPECTED_HELPERS: Final[tuple[str, ...]] = (
    "_require_text",
    "_require_probability",
    "canonicalize",
    "canonical_fingerprint",
)


@dataclass(frozen=True, slots=True)
class FieldRecord:
    """One annotated field discovered on a contract class."""

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
class ContractRecord:
    """Structural audit information for one reasoning contract."""

    name: str
    docstring: str
    frozen: bool
    slots: bool
    fields: tuple[FieldRecord, ...]
    methods: tuple[str, ...]
    properties: tuple[str, ...]
    has_post_init: bool
    has_to_dict: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "docstring": self.docstring,
            "frozen": self.frozen,
            "slots": self.slots,
            "fields": [field.to_dict() for field in self.fields],
            "methods": list(self.methods),
            "properties": list(self.properties),
            "has_post_init": self.has_post_init,
            "has_to_dict": self.has_to_dict,
        }


def _unparse(node: ast.AST | None) -> str:
    """Return a stable source representation for an AST node."""

    if node is None:
        return ""
    return ast.unparse(node)


def _decorator_name(decorator: ast.expr) -> str:
    """Return the canonical name of a decorator expression."""

    if isinstance(decorator, ast.Name):
        return decorator.id

    if isinstance(decorator, ast.Attribute):
        return decorator.attr

    if isinstance(decorator, ast.Call):
        return _decorator_name(decorator.func)

    return _unparse(decorator)


def _dataclass_configuration(
    node: ast.ClassDef,
) -> tuple[bool, bool, bool]:
    """Return whether a class is a dataclass and its frozen/slots settings."""

    for decorator in node.decorator_list:
        if isinstance(decorator, ast.Call):
            if _decorator_name(decorator.func) != "dataclass":
                continue

            keyword_values = {
                keyword.arg: keyword.value
                for keyword in decorator.keywords
                if keyword.arg is not None
            }

            frozen = (
                isinstance(keyword_values.get("frozen"), ast.Constant)
                and keyword_values["frozen"].value is True
            )
            slots = (
                isinstance(keyword_values.get("slots"), ast.Constant)
                and keyword_values["slots"].value is True
            )
            return True, frozen, slots

        if _decorator_name(decorator) == "dataclass":
            return True, False, False

    return False, False, False


def _class_fields(node: ast.ClassDef) -> tuple[FieldRecord, ...]:
    """Extract annotated dataclass fields in declaration order."""

    records: list[FieldRecord] = []

    for statement in node.body:
        if not isinstance(statement, ast.AnnAssign):
            continue

        if not isinstance(statement.target, ast.Name):
            continue

        records.append(
            FieldRecord(
                name=statement.target.id,
                annotation=_unparse(statement.annotation),
                has_default=statement.value is not None,
            )
        )

    return tuple(records)


def _class_methods(
    node: ast.ClassDef,
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Return ordinary method names and property names."""

    methods: list[str] = []
    properties: list[str] = []

    for statement in node.body:
        if not isinstance(
            statement,
            (ast.FunctionDef, ast.AsyncFunctionDef),
        ):
            continue

        decorator_names = {
            _decorator_name(decorator)
            for decorator in statement.decorator_list
        }

        if "property" in decorator_names:
            properties.append(statement.name)
        else:
            methods.append(statement.name)

    return tuple(methods), tuple(properties)


def _imported_reasoning_enums(tree: ast.Module) -> tuple[str, ...]:
    """Return names imported from the canonical reasoning enums module."""

    names: list[str] = []

    for statement in tree.body:
        if not isinstance(statement, ast.ImportFrom):
            continue

        if statement.module != "core.reasoning.enums":
            continue

        names.extend(alias.name for alias in statement.names)

    return tuple(sorted(names))


def _module_functions(tree: ast.Module) -> tuple[str, ...]:
    """Return top-level function names in source order."""

    return tuple(
        statement.name
        for statement in tree.body
        if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef))
    )


def _contract_records(tree: ast.Module) -> tuple[ContractRecord, ...]:
    """Return immutable contract records from the models module."""

    records: list[ContractRecord] = []

    for statement in tree.body:
        if not isinstance(statement, ast.ClassDef):
            continue

        is_dataclass, frozen, slots = _dataclass_configuration(statement)
        if not is_dataclass:
            continue

        methods, properties = _class_methods(statement)

        records.append(
            ContractRecord(
                name=statement.name,
                docstring=ast.get_docstring(statement) or "",
                frozen=frozen,
                slots=slots,
                fields=_class_fields(statement),
                methods=methods,
                properties=properties,
                has_post_init="__post_init__" in methods,
                has_to_dict="to_dict" in methods,
            )
        )

    return tuple(records)


def _field_names(
    contracts: tuple[ContractRecord, ...],
    contract_name: str,
) -> tuple[str, ...]:
    """Return field names for one contract."""

    for contract in contracts:
        if contract.name == contract_name:
            return tuple(field.name for field in contract.fields)

    return ()


def build_report() -> dict[str, Any]:
    """Build the complete deterministic contract-audit report."""

    if not SOURCE_PATH.is_file():
        raise FileNotFoundError(
            f"Reasoning contract source not found: {SOURCE_PATH}"
        )

    source = SOURCE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(SOURCE_PATH))

    contracts = _contract_records(tree)
    module_functions = _module_functions(tree)
    contract_names = tuple(contract.name for contract in contracts)

    missing_expected_contracts = sorted(
        set(EXPECTED_CONTRACTS).difference(contract_names)
    )
    unexpected_contracts = sorted(
        set(contract_names).difference(EXPECTED_CONTRACTS)
    )
    missing_expected_helpers = sorted(
        set(EXPECTED_HELPERS).difference(module_functions)
    )

    immutable_contracts = all(
        contract.frozen and contract.slots
        for contract in contracts
    )
    serializable_contracts = all(
        contract.has_to_dict
        for contract in contracts
    )

    evidence_fields = _field_names(contracts, "EvidenceItem")
    request_fields = _field_names(contracts, "ReasoningRequest")
    result_fields = _field_names(contracts, "ReasoningResult")

    evidence_has_weight_property = any(
        contract.name == "EvidenceItem"
        and "weight" in contract.properties
        for contract in contracts
    )
    request_has_fingerprint_property = any(
        contract.name == "ReasoningRequest"
        and "fingerprint" in contract.properties
        for contract in contracts
    )

    conclusions = {
        "canonical_contract_module_present": True,
        "expected_contracts_present": not missing_expected_contracts,
        "all_contracts_frozen_and_slotted": immutable_contracts,
        "all_contracts_serializable": serializable_contracts,
        "canonical_serialization_present": (
            "canonicalize" in module_functions
            and "canonical_fingerprint" in module_functions
        ),
        "evidence_weight_present": evidence_has_weight_property,
        "request_fingerprint_present": request_has_fingerprint_property,
        "evidence_model_is_embedded_in_models_module": (
            "EvidenceItem" in contract_names
        ),
        "reasoning_session_input_present": (
            "ReasoningRequest" in contract_names
        ),
        "reasoning_session_output_present": (
            "ReasoningResult" in contract_names
        ),
        "planning_bridge_present": (
            "PlanningRecommendation" in contract_names
        ),
    }

    migration_observations = (
        "EvidenceItem is already the canonical evidence contract; Genesis "
        "must evolve it rather than introduce a competing evidence model.",
        "ReasoningRequest already represents a deterministic session input "
        "and includes a canonical fingerprint.",
        "ReasoningResult already represents a complete reasoning-session "
        "output, including traceability and a planning bridge.",
        "All current contracts use frozen, slotted dataclasses and should "
        "retain those immutability guarantees.",
        "Canonical serialization and SHA-256 fingerprinting are established "
        "cross-contract infrastructure and should remain backward compatible.",
        "Future evidence provenance, admission, and assessment contracts "
        "should integrate with EvidenceItem through deliberate migration.",
    )

    return {
        "audit_id": "GENESIS-I-A1",
        "title": "Reasoning Contract Audit",
        "source": str(SOURCE_PATH.relative_to(PROJECT_ROOT)),
        "contract_count": len(contracts),
        "contracts": [contract.to_dict() for contract in contracts],
        "module_functions": list(module_functions),
        "imported_reasoning_enums": list(
            _imported_reasoning_enums(tree)
        ),
        "expected_contracts": list(EXPECTED_CONTRACTS),
        "missing_expected_contracts": missing_expected_contracts,
        "unexpected_contracts": unexpected_contracts,
        "missing_expected_helpers": missing_expected_helpers,
        "key_field_inventories": {
            "EvidenceItem": list(evidence_fields),
            "ReasoningRequest": list(request_fields),
            "ReasoningResult": list(result_fields),
        },
        "conclusions": conclusions,
        "migration_observations": list(migration_observations),
    }


def render_json(report: dict[str, Any]) -> str:
    """Render the canonical JSON report."""

    return json.dumps(
        report,
        indent=2,
        sort_keys=True,
        ensure_ascii=True,
    ) + "\n"


def _yes_no(value: bool) -> str:
    return "Yes" if value else "No"


def render_markdown(report: dict[str, Any]) -> str:
    """Render the human-readable Markdown report."""

    lines: list[str] = [
        "# Genesis I-A1 — Reasoning Contract Audit",
        "",
        "**Status:** Architecture baseline  ",
        "**Scope:** `core/reasoning/models.py`  ",
        "**Production code modified:** No",
        "",
        "## Purpose",
        "",
        "This audit records the canonical contract architecture that existed "
        "before Genesis evidence-model evolution began. It is a deterministic "
        "baseline, not a redesign.",
        "",
        "## Executive Finding",
        "",
        "The Reasoning Engine already contains a coherent immutable contract "
        "model. Genesis must evolve these contracts deliberately rather than "
        "introducing a parallel evidence or session architecture.",
        "",
        "## Contract Inventory",
        "",
        "| Contract | Fields | Frozen | Slotted | `to_dict()` | "
        "`__post_init__()` |",
        "|---|---:|:---:|:---:|:---:|:---:|",
    ]

    for contract in report["contracts"]:
        lines.append(
            "| `{name}` | {field_count} | {frozen} | {slots} | "
            "{to_dict} | {post_init} |".format(
                name=contract["name"],
                field_count=len(contract["fields"]),
                frozen=_yes_no(contract["frozen"]),
                slots=_yes_no(contract["slots"]),
                to_dict=_yes_no(contract["has_to_dict"]),
                post_init=_yes_no(contract["has_post_init"]),
            )
        )

    lines.extend(
        [
            "",
            "## Detailed Contracts",
            "",
        ]
    )

    for contract in report["contracts"]:
        lines.extend(
            [
                f"### `{contract['name']}`",
                "",
                contract["docstring"] or "_No class docstring._",
                "",
                "**Fields**",
                "",
            ]
        )

        for field in contract["fields"]:
            default_suffix = " — defaulted" if field["has_default"] else ""
            lines.append(
                f"- `{field['name']}: {field['annotation']}`"
                f"{default_suffix}"
            )

        lines.extend(
            [
                "",
                "**Methods:** "
                + (
                    ", ".join(
                        f"`{name}()`" for name in contract["methods"]
                    )
                    if contract["methods"]
                    else "None"
                ),
                "",
                "**Properties:** "
                + (
                    ", ".join(
                        f"`{name}`" for name in contract["properties"]
                    )
                    if contract["properties"]
                    else "None"
                ),
                "",
            ]
        )

    lines.extend(
        [
            "## Canonical Infrastructure",
            "",
            "Top-level model helpers:",
            "",
        ]
    )

    for function_name in report["module_functions"]:
        lines.append(f"- `{function_name}()`")

    lines.extend(
        [
            "",
            "Imported reasoning enumerations:",
            "",
        ]
    )

    for enum_name in report["imported_reasoning_enums"]:
        lines.append(f"- `{enum_name}`")

    lines.extend(
        [
            "",
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
            "## Genesis Migration Observations",
            "",
        ]
    )

    for observation in report["migration_observations"]:
        lines.append(f"- {observation}")

    lines.extend(
        [
            "",
            "## Architectural Decision",
            "",
            "`core/reasoning/models.py` remains the canonical reasoning-contract "
            "module during the first Genesis increment. No competing "
            "`core/reasoning/evidence/` package will be introduced until a "
            "specific migration requirement justifies it.",
            "",
            "The next audit increment should inspect orchestration in "
            "`core/reasoning/service.py` and determine how the existing "
            "contracts participate in a complete reasoning session.",
            "",
        ]
    )

    return "\n".join(lines)


def _check_file(path: Path, expected: str) -> bool:
    """Return whether a generated report exists and is current."""

    if not path.is_file():
        print(f"[FAIL] Missing generated report: {path.relative_to(PROJECT_ROOT)}")
        return False

    actual = path.read_text(encoding="utf-8")

    if actual != expected:
        print(f"[FAIL] Stale generated report: {path.relative_to(PROJECT_ROOT)}")
        return False

    print(f"[PASS] Current report: {path.relative_to(PROJECT_ROOT)}")
    return True


def write_reports(json_content: str, markdown_content: str) -> None:
    """Write both deterministic audit reports."""

    JSON_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    MARKDOWN_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)

    JSON_REPORT_PATH.write_text(json_content, encoding="utf-8")
    MARKDOWN_REPORT_PATH.write_text(markdown_content, encoding="utf-8")

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
        description="Audit the canonical Reasoning Engine contracts."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail if generated reports are missing or stale.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    try:
        report = build_report()
    except (OSError, SyntaxError) as exc:
        print(f"[FAIL] Unable to audit reasoning contracts: {exc}")
        return 1

    json_content = render_json(report)
    markdown_content = render_markdown(report)

    if args.check:
        json_current = _check_file(JSON_REPORT_PATH, json_content)
        markdown_current = _check_file(
            MARKDOWN_REPORT_PATH,
            markdown_content,
        )
        return 0 if json_current and markdown_current else 1

    write_reports(json_content, markdown_content)

    print(
        "[PASS] Audited "
        f"{report['contract_count']} reasoning contracts"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
PYEOF

cat > dev/verify_genesis_1a1.sh <<'VERIFYEOF'
#!/usr/bin/env bash

set -euo pipefail

PROJECT_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
PYTHON_BIN="${PYTHON_BIN:-python}"

cd "$PROJECT_ROOT"

echo
echo "======================================================================"
echo "JARVIS GEN 2 — GENESIS I-A1"
echo "REASONING CONTRACT AUDIT"
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

check_file "core/reasoning/models.py"
check_file "dev/tools/audit_reasoning_contracts.py"
check_file "dev/verify_genesis_1a1.sh"

if "$PYTHON_BIN" -m py_compile \
    core/reasoning/models.py \
    dev/tools/audit_reasoning_contracts.py
then
    pass "Reasoning contracts and audit tool compile"
else
    fail "Reasoning contracts and audit tool compile"
fi

if "$PYTHON_BIN" dev/tools/audit_reasoning_contracts.py; then
    pass "Reasoning contract audit generated"
else
    fail "Reasoning contract audit generated"
fi

check_file \
    "docs/architecture/convergence/genesis_1a1_reasoning_contract_audit.json"
check_file \
    "docs/architecture/convergence/genesis_1a1_reasoning_contract_audit.md"

if "$PYTHON_BIN" dev/tools/audit_reasoning_contracts.py --check; then
    pass "Generated audit reports are deterministic and current"
else
    fail "Generated audit reports are deterministic and current"
fi

if "$PYTHON_BIN" - <<'PY'
from __future__ import annotations

import json
from pathlib import Path

from core.reasoning.models import (
    EvidenceItem,
    Hypothesis,
    HypothesisAssessment,
    PlanningRecommendation,
    ReasoningRequest,
    ReasoningResult,
    ReasoningTraceStep,
    canonical_fingerprint,
    canonicalize,
)

report_path = Path(
    "docs/architecture/convergence/"
    "genesis_1a1_reasoning_contract_audit.json"
)
report = json.loads(report_path.read_text(encoding="utf-8"))

expected_contracts = {
    "EvidenceItem",
    "Hypothesis",
    "ReasoningRequest",
    "HypothesisAssessment",
    "ReasoningTraceStep",
    "PlanningRecommendation",
    "ReasoningResult",
}

actual_contracts = {
    contract["name"]
    for contract in report["contracts"]
}

assert actual_contracts == expected_contracts
assert report["contract_count"] == 7
assert report["missing_expected_contracts"] == []
assert report["missing_expected_helpers"] == []

for contract in report["contracts"]:
    assert contract["frozen"] is True
    assert contract["slots"] is True
    assert contract["has_to_dict"] is True

assert report["conclusions"]["canonical_serialization_present"] is True
assert report["conclusions"]["evidence_weight_present"] is True
assert report["conclusions"]["request_fingerprint_present"] is True
assert report["conclusions"]["planning_bridge_present"] is True

assert callable(canonicalize)
assert callable(canonical_fingerprint)

assert EvidenceItem is not None
assert Hypothesis is not None
assert ReasoningRequest is not None
assert HypothesisAssessment is not None
assert ReasoningTraceStep is not None
assert PlanningRecommendation is not None
assert ReasoningResult is not None

print("[PASS] Canonical reasoning-contract assertions")
PY
then
    pass "Canonical contract structure"
else
    fail "Canonical contract structure"
fi

if "$PYTHON_BIN" - <<'PY'
from core.reasoning.enums import EvidenceKind, EvidenceStance
from core.reasoning.models import (
    EvidenceItem,
    Hypothesis,
    ReasoningRequest,
)

evidence = EvidenceItem(
    evidence_id="evidence-001",
    proposition="The observed condition is present.",
    stance=EvidenceStance.SUPPORTS,
    source_ref="verification-fixture",
    kind=EvidenceKind.FACT,
    reliability=0.8,
    confidence=0.75,
)

assert evidence.weight == 0.6

hypothesis = Hypothesis(
    hypothesis_id="hypothesis-001",
    statement="The observed condition explains the target outcome.",
    supporting_evidence_ids=(evidence.evidence_id,),
)

request = ReasoningRequest(
    request_id="request-001",
    goal="Assess the target explanation.",
    evidence=(evidence,),
    hypotheses=(hypothesis,),
)

first_fingerprint = request.fingerprint
second_fingerprint = request.fingerprint

assert len(first_fingerprint) == 64
assert first_fingerprint == second_fingerprint
assert request.to_dict()["request_id"] == "request-001"

print("[PASS] Immutable reasoning-contract smoke test")
PY
then
    pass "Reasoning-contract smoke test"
else
    fail "Reasoning-contract smoke test"
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

chmod +x dev/tools/audit_reasoning_contracts.py
chmod +x dev/verify_genesis_1a1.sh

echo "[CREATE] dev/tools/audit_reasoning_contracts.py"
echo "[CREATE] dev/verify_genesis_1a1.sh"

echo
echo "[PASS] Genesis I-A1 audit tooling installed"
echo
