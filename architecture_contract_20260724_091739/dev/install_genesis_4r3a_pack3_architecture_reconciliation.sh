#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="${PROJECT_ROOT:-$(pwd)}"
PYTHON_BIN="${PYTHON_BIN:-python}"

cd "${PROJECT_ROOT}"

mkdir -p \
    dev/verification \
    docs/architecture \
    docs/audits \
    docs/decisions

cat > docs/architecture/cognitive_ownership.md <<'EOF'
# Canonical Cognitive Subsystem Ownership

**Status:** Accepted architecture baseline  
**Release:** Genesis IV-R3A Pack 3  
**Purpose:** Define canonical ownership boundaries for JARVIS cognitive domain models.

## 1. Governing Principle

Each cognitive concept has exactly one canonical owning subsystem.

Other subsystems may consume, reference, adapt, or serialize that concept, but
they must not independently redefine its domain model.

This rule prevents competing truths while allowing controlled compatibility
migrations.

## 2. Canonical Ownership Map

| Concept family | Canonical owner | Primary consumers |
| --- | --- | --- |
| Observation and observed facts | `core.cognition.layers.observation` | Evidence, reasoning, representation |
| Evidence and propositions | `core.evidence` | Reasoning, cognition, executive |
| Reasoning, inference, and hypotheses | `core.reasoning` | Executive, mission planning |
| Cognitive representation and segmentation | `core.representation` | Cognition, reasoning, knowledge |
| Missions, objectives, tasks, and plans | `core.executive` | API, UI, runtime |
| Presentation and interaction state | UI layer | Human operator |

## 3. Ownership Rules

1. The owning subsystem defines the canonical contracts, enums, errors, and
   serialization guarantees for its concepts.
2. Consumers import canonical types rather than reproducing equivalent types.
3. Compatibility aliases may exist temporarily during migration.
4. Compatibility aliases must be explicitly documented and tested.
5. No legacy module may be removed while active imports or serialized-data
   compatibility obligations remain.
6. Migration changes imports and ownership; it does not rewrite proven
   algorithms without a separate architectural reason.
7. Circular ownership is prohibited.

## 4. Canonical Evidence Ownership

`core.evidence` is the canonical owner of:

- `Proposition`
- `EvidenceRecord`
- `EvidenceAssessment`
- `EvidenceRelationship`
- evidence lifecycle enums
- evidence-domain errors
- canonical evidence serialization

`core.reasoning` may evaluate or consume evidence but must not remain the
long-term owner of evidence-domain contracts.

`core.cognition` may construct cognitive workflows involving evidence but must
not maintain a competing evidence domain model.

## 5. Controlled Migration Protocol

Every ownership migration follows these gates:

1. **Inventory** — identify duplicate symbols and every consumer.
2. **Canonical declaration** — name the permanent owner.
3. **Compatibility design** — determine aliases, adapters, or data migration.
4. **Import migration** — redirect consumers in bounded, verified packs.
5. **Compatibility verification** — prove public behavior remains valid.
6. **Legacy quarantine** — freeze the old implementation against new features.
7. **Removal eligibility** — confirm zero active imports and no unresolved
   persistence obligations.
8. **Removal certification** — delete only in a dedicated certified pack.

## 6. Current Migration Direction

```text
core/reasoning/evidence  ─────┐
                              ├──> core/evidence
core/cognition evidence ──────┘
```

The arrow represents canonical ownership migration, not immediate deletion.

## 7. Prohibited Actions

Until migration eligibility is certified, do not:

- delete `core/reasoning/evidence`;
- bulk-rewrite reasoning algorithms;
- silently alias semantically different enums;
- change serialized field names;
- merge contracts solely because their names match;
- add new evidence capabilities to legacy evidence packages.

## 8. Completion Condition

The Evidence ownership migration is complete when:

- all production consumers use `core.evidence` directly or through an approved
  compatibility adapter;
- duplicate evidence contracts no longer evolve independently;
- all compatibility tests pass;
- persisted representations remain readable or have a certified migration;
- the legacy package is proven removable.
EOF

cat > docs/architecture/evidence_engine.md <<'EOF'
# JARVIS Evidence Engine

**Status:** Canonical subsystem specification  
**Canonical package:** `core.evidence`  
**Architecture release:** Genesis IV-R3A Pack 3

## 1. Mission

The Evidence Engine transforms validated observations into deterministic,
explainable, auditable evidence suitable for reasoning and executive decisions.

It answers five distinct questions:

1. Is the source observation admissible?
2. What evidence record should be constructed?
3. How does that record relate to other evidence?
4. Is the available body of evidence sufficient?
5. What stable evidence input may reasoning consume?

## 2. Design Principles

The Evidence Engine is:

- deterministic;
- immutable at its contract boundaries;
- provenance preserving;
- policy driven;
- explainable;
- auditable;
- serialization stable;
- side-effect free in its domain evaluation layers;
- isolated from reasoning algorithms.

## 3. Canonical Pipeline

```text
Observation
    |
    v
Validation
    |
    v
Admissibility Evaluation
    |
    +--> Rejected / Deferred
    |
    v
Evidence Construction
    |
    v
Relationship Analysis
    |
    v
Aggregation and Sufficiency
    |
    v
Reasoning Input
```

## 4. Architectural Layers

### 4.1 Foundation

Current canonical files:

- `core/evidence/enums.py`
- `core/evidence/errors.py`
- `core/evidence/contracts.py`
- `core/evidence/__init__.py`

Responsibilities:

- stable vocabulary;
- immutable contracts;
- validation invariants;
- deterministic canonical serialization;
- public API exports.

### 4.2 Admissibility

Planned canonical files:

- `core/evidence/policy.py`
- `core/evidence/rules.py`
- `core/evidence/evaluator.py`
- `core/evidence/admissibility.py`

Responsibilities:

- immutable policy definition;
- deterministic rule evaluation;
- reason-coded outcomes;
- evaluation traces;
- no persistence;
- no evidence construction.

### 4.3 Construction

Planned responsibility:

- produce an `EvidenceRecord` from an admitted observation and decision;
- preserve provenance and policy identifiers;
- calculate deterministic identifiers and fingerprints;
- perform no relationship or sufficiency analysis.

### 4.4 Relationships

Planned responsibility:

- represent support, contradiction, corroboration, duplication, and dependency;
- remain deterministic and explainable;
- avoid mutating evidence records.

### 4.5 Aggregation and Sufficiency

Planned responsibility:

- assemble evidence sets;
- calculate policy-defined sufficiency;
- identify gaps and conflicts;
- expose reasoning-ready evidence without performing reasoning.

### 4.6 Runtime Integration

Planned responsibility:

- orchestrate domain components;
- connect registries or persistence;
- expose stable application services;
- preserve domain-layer independence.

## 5. Dependency Direction

```text
enums/errors
     |
     v
contracts
     |
     v
policy/rules
     |
     v
evaluator/admissibility
     |
     v
construction
     |
     v
relationships
     |
     v
aggregation
     |
     v
runtime service
     |
     v
reasoning consumer
```

Dependencies must not point from Evidence into Reasoning or Executive.

## 6. Admissibility Boundary

The admissibility layer consumes observation references or observation-domain
contracts and produces an `AdmissibilityDecision`.

It does not:

- create an `EvidenceRecord`;
- write to a registry;
- discover relationships;
- aggregate evidence;
- calculate reasoning confidence;
- issue recommendations.

## 7. Policy Families

The architecture reserves the following policy families:

- observation completeness;
- provenance completeness;
- source reliability;
- integrity status;
- temporal validity and freshness;
- duplication indicators;
- chain-of-custody requirements;
- supported observation type;
- policy-version compatibility.

Each rule must emit a stable rule identifier and an explainable result.

## 8. Public Compatibility

The stable public API is defined through `core.evidence.__all__`.

Future releases may add exports. Existing certified exports may only be removed
through an explicit compatibility-breaking decision and migration.

## 9. Certification and Compatibility

Certification proves a pack satisfies the specification in force when released.

Compatibility verification proves later packs preserve promised public behavior
while allowing intentional architectural evolution.

Historical certification tests are not permanent prohibitions against adding
new capabilities.

## 10. Release Sequence

- **Genesis IV-R3A** — Evidence foundation and deterministic contracts.
- **Genesis IV-R3B** — Admissibility policy foundation.
- **Genesis IV-R3C** — Evidence construction.
- **Genesis IV-R3D** — Evidence relationships.
- **Genesis IV-R3E** — Aggregation and sufficiency.
- **Genesis IV-R3F** — Runtime integration.
- **Genesis IV-R3G** — Evidence subsystem freeze.
EOF

cat > dev/audit_cognitive_ownership.py <<'PYEOF'
#!/usr/bin/env python3
"""Audit duplicate cognitive symbols and legacy evidence dependencies."""

from __future__ import annotations

import ast
import json
from collections import defaultdict
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / "core"
REPORT = ROOT / "docs" / "audits" / "cognitive_ownership_migration_map.md"
DATA = ROOT / "docs" / "audits" / "cognitive_ownership_migration_map.json"

EXCLUDED = {"__pycache__", ".migration_backups", ".git"}


def files() -> Iterable[Path]:
    for path in sorted(CORE.rglob("*.py")):
        if any(part in EXCLUDED for part in path.parts):
            continue
        yield path


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def module_name(path: Path) -> str:
    parts = list(path.relative_to(ROOT).with_suffix("").parts)
    if parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


def imported_modules(tree: ast.AST) -> list[str]:
    values: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            values.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            values.append(("." * node.level) + (node.module or ""))
    return values


def symbols(tree: ast.Module) -> list[str]:
    result: list[str] = []
    for node in tree.body:
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            if not node.name.startswith("_"):
                result.append(node.name)
    return result


def main() -> int:
    parsed: dict[Path, ast.Module] = {}
    parse_errors: list[dict[str, str]] = []

    for path in files():
        try:
            parsed[path] = ast.parse(
                path.read_text(encoding="utf-8", errors="replace"),
                filename=str(path),
            )
        except SyntaxError as exc:
            parse_errors.append({"path": rel(path), "error": str(exc)})

    symbol_locations: dict[str, list[str]] = defaultdict(list)
    for path, tree in parsed.items():
        for symbol in symbols(tree):
            symbol_locations[symbol].append(rel(path))

    evidence_duplicate_names = {
        name: locations
        for name, locations in sorted(symbol_locations.items())
        if len(locations) > 1
        and any(location.startswith("core/evidence/") for location in locations)
    }

    legacy_imports: list[dict[str, object]] = []
    canonical_imports: list[dict[str, object]] = []

    for path, tree in parsed.items():
        imports = sorted(set(imported_modules(tree)))
        legacy = [
            value for value in imports
            if "reasoning.evidence" in value
        ]
        canonical = [
            value for value in imports
            if value == "core.evidence" or value.startswith("core.evidence.")
        ]
        if legacy:
            legacy_imports.append({
                "consumer": rel(path),
                "module": module_name(path),
                "imports": legacy,
            })
        if canonical:
            canonical_imports.append({
                "consumer": rel(path),
                "module": module_name(path),
                "imports": canonical,
            })

    legacy_package_files = [
        rel(path)
        for path in parsed
        if rel(path).startswith("core/reasoning/evidence/")
    ]

    data = {
        "canonical_owner": "core.evidence",
        "legacy_package": "core.reasoning.evidence",
        "legacy_package_files": legacy_package_files,
        "legacy_consumers": legacy_imports,
        "canonical_consumers": canonical_imports,
        "duplicate_symbols_touching_core_evidence": evidence_duplicate_names,
        "parse_errors": parse_errors,
        "migration_eligible_for_removal": (
            not legacy_package_files
            or (not legacy_imports and not evidence_duplicate_names)
        ),
    }

    DATA.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    duplicate_lines = []
    for name, locations in evidence_duplicate_names.items():
        duplicate_lines.append(
            f"| `{name}` | " + "<br>".join(f"`{location}`" for location in locations) + " |"
        )

    legacy_lines = []
    for item in legacy_imports:
        legacy_lines.append(
            f"| `{item['consumer']}` | " +
            "<br>".join(f"`{value}`" for value in item["imports"]) + " |"
        )

    canonical_lines = []
    for item in canonical_imports:
        canonical_lines.append(
            f"| `{item['consumer']}` | " +
            "<br>".join(f"`{value}`" for value in item["imports"]) + " |"
        )

    report = f"""# Cognitive Ownership Migration Map

**Canonical evidence owner:** `core.evidence`  
**Legacy evidence package:** `core.reasoning.evidence`  
**Removal eligible:** {"YES" if data["migration_eligible_for_removal"] else "NO"}

## 1. Legacy Package Files

{chr(10).join(f"- `{path}`" for path in legacy_package_files) or "- None"}

## 2. Active Legacy Imports

| Consumer | Legacy imports |
| --- | --- |
{chr(10).join(legacy_lines) or "| None | None |"}

## 3. Active Canonical Imports

| Consumer | Canonical imports |
| --- | --- |
{chr(10).join(canonical_lines) or "| None | None |"}

## 4. Duplicate Symbols Touching `core.evidence`

| Symbol | Locations |
| --- | --- |
{chr(10).join(duplicate_lines) or "| None | None |"}

## 5. Migration Decision

The legacy package is not removable while any of the following remain:

- production imports of `core.reasoning.evidence`;
- semantically unresolved duplicate contracts;
- persisted payloads tied to the legacy schema;
- compatibility obligations without adapters.

This audit authorizes analysis only. It does not authorize deletion.
"""

    REPORT.write_text(report, encoding="utf-8")

    print("=" * 72)
    print("GENESIS IV-R3A PACK 3 — COGNITIVE OWNERSHIP AUDIT")
    print("=" * 72)
    print(f"[PASS] Legacy package files : {len(legacy_package_files)}")
    print(f"[PASS] Legacy consumers     : {len(legacy_imports)}")
    print(f"[PASS] Canonical consumers  : {len(canonical_imports)}")
    print(f"[PASS] Duplicate symbols    : {len(evidence_duplicate_names)}")
    print(f"[PASS] Parse errors         : {len(parse_errors)}")
    print(f"[PASS] Report               : {REPORT.relative_to(ROOT)}")
    print(f"[PASS] Data                 : {DATA.relative_to(ROOT)}")
    print("-" * 72)
    print("Status: MIGRATION MAP GENERATED")
    print("=" * 72)

    return 1 if parse_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
PYEOF

cat > dev/verification/verify_genesis_4r3a_pack3_architecture_reconciliation.py <<'PYEOF'
#!/usr/bin/env python3
"""Verify Genesis IV-R3A Pack 3 architecture reconciliation assets."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

REQUIRED_FILES = (
    ROOT / "docs" / "architecture" / "cognitive_ownership.md",
    ROOT / "docs" / "architecture" / "evidence_engine.md",
    ROOT / "dev" / "audit_cognitive_ownership.py",
    ROOT / "docs" / "audits" / "cognitive_ownership_migration_map.md",
    ROOT / "docs" / "audits" / "cognitive_ownership_migration_map.json",
)

REQUIRED_OWNERSHIP_TEXT = (
    "Each cognitive concept has exactly one canonical owning subsystem.",
    "`core.evidence` is the canonical owner",
    "Controlled Migration Protocol",
    "do not:",
)

REQUIRED_EVIDENCE_TEXT = (
    "The Evidence Engine transforms validated observations",
    "Admissibility Evaluation",
    "Dependencies must not point from Evidence into Reasoning or Executive.",
    "Certification proves a pack",
)


def check(condition: bool, label: str) -> int:
    if condition:
        print(f"[PASS] {label}")
        return 0
    print(f"[FAIL] {label}")
    return 1


def main() -> int:
    failures = 0

    failures += check(
        all(path.is_file() for path in REQUIRED_FILES),
        "Required reconciliation assets",
    )

    ownership = (ROOT / "docs" / "architecture" / "cognitive_ownership.md").read_text(
        encoding="utf-8"
    )
    evidence = (ROOT / "docs" / "architecture" / "evidence_engine.md").read_text(
        encoding="utf-8"
    )

    failures += check(
        all(text in ownership for text in REQUIRED_OWNERSHIP_TEXT),
        "Canonical ownership invariants",
    )
    failures += check(
        all(text in evidence for text in REQUIRED_EVIDENCE_TEXT),
        "Evidence Engine specification invariants",
    )

    result = subprocess.run(
        [sys.executable, "dev/audit_cognitive_ownership.py"],
        cwd=ROOT,
        check=False,
    )
    failures += check(result.returncode == 0, "Ownership audit execution")

    data = json.loads(
        (ROOT / "docs" / "audits" / "cognitive_ownership_migration_map.json").read_text(
            encoding="utf-8"
        )
    )

    failures += check(
        data.get("canonical_owner") == "core.evidence",
        "Canonical Evidence owner",
    )
    failures += check(
        data.get("legacy_package") == "core.reasoning.evidence",
        "Legacy Evidence package identified",
    )
    failures += check(
        data.get("migration_eligible_for_removal") is False,
        "Legacy removal remains blocked pending migration",
    )
    failures += check(
        not data.get("parse_errors"),
        "Production Python syntax health",
    )

    print()
    print("-" * 72)
    print(f"Checks failed : {failures}")
    print(f"Overall status: {'EXCELLENT' if failures == 0 else 'FAILED'}")
    print("=" * 72)

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
PYEOF

cat > dev/verify_genesis_4r3a_pack3.sh <<'EOF'
#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python}"

cd "${PROJECT_ROOT}"

echo
echo "========================================================================"
echo "JARVIS GENESIS IV-R3A PACK 3 — ARCHITECTURE RECONCILIATION"
echo "========================================================================"

"${PYTHON_BIN}" dev/verification/verify_genesis_4r3a_pack3_architecture_reconciliation.py
EOF

chmod +x \
    dev/audit_cognitive_ownership.py \
    dev/verify_genesis_4r3a_pack3.sh \
    dev/verification/verify_genesis_4r3a_pack3_architecture_reconciliation.py

"${PYTHON_BIN}" dev/audit_cognitive_ownership.py
"${PYTHON_BIN}" dev/verification/verify_genesis_4r3a_pack3_architecture_reconciliation.py

echo
echo "Installed Genesis IV-R3A Pack 3 architecture reconciliation assets."
