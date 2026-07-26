#!/usr/bin/env bash
#
# JARVIS — CONST-0001 Constitutional Compliance Matrix Installer
#
# Inserts the populated Article I–XIX compliance matrix immediately after:
#
#   Observation → Verification → Certification → Operational Learning
#
# and immediately before:
#
#   Every Article shall map to responsible packages...
#

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONSTITUTION="${PROJECT_ROOT}/docs/constitution/executive.md"
BACKUP_ROOT="${PROJECT_ROOT}/.migration_backups"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP_DIR="${BACKUP_ROOT}/const_0001_matrix_${TIMESTAMP}"
BACKUP_FILE="${BACKUP_DIR}/executive.md"

echo "========================================================================"
echo "JARVIS — CONST-0001 CONSTITUTIONAL COMPLIANCE MATRIX"
echo "========================================================================"

if [[ ! -f "${CONSTITUTION}" ]]; then
    echo "[FAIL] Constitution not found:"
    echo "       ${CONSTITUTION}"
    exit 1
fi

mkdir -p "${BACKUP_DIR}"
cp "${CONSTITUTION}" "${BACKUP_FILE}"

echo "[PASS] Backup created:"
echo "       ${BACKUP_FILE}"

CONSTITUTION_PATH="${CONSTITUTION}" python3 <<'PY'
from __future__ import annotations

import os
from pathlib import Path


path = Path(os.environ["CONSTITUTION_PATH"])
text = path.read_text(encoding="utf-8")

lifecycle_anchor = (
    "Observation → Verification → Certification → Operational Learning"
)

next_section_anchor = (
    "Every Article shall map to responsible packages, ADRs, verification suites,"
)

matrix_heading = "## Constitutional Compliance Matrix"

if matrix_heading in text:
    raise SystemExit(
        "[FAIL] Constitutional Compliance Matrix already exists. "
        "No changes were made."
    )

lifecycle_index = text.find(lifecycle_anchor)

if lifecycle_index == -1:
    raise SystemExit(
        "[FAIL] Governance Lifecycle anchor was not found:\n"
        f"       {lifecycle_anchor}"
    )

insert_start = lifecycle_index + len(lifecycle_anchor)
next_section_index = text.find(next_section_anchor, insert_start)

if next_section_index == -1:
    raise SystemExit(
        "[FAIL] The expected following paragraph was not found:\n"
        f"       {next_section_anchor}"
    )

matrix = r"""

---

## Constitutional Compliance Matrix

This matrix establishes the initial constitutional traceability baseline for Articles I–XIX.

A status of **Mapped** means that governing doctrine and one or more implementation or verification artifacts already exist.

A status of **Partial** means that relevant implementation exists, but Article-specific constitutional verification is not yet complete.

A status of **Pending G2** means that formal enforcement, automated traceability, or certification shall be implemented by the Constitutional Enforcement Engine.

| Article | Responsible Package or Authority | Governing ADRs and Whitepapers | Architecture and Constitutional Specifications | Verification and Certification Evidence | Primary Implementation Modules and Public Surfaces | Executive Capability | Status and Architectural Notes |
|---|---|---|---|---|---|---|---|
| **I — Constitutional Authority** | `docs/constitution`; `core/executive` | `ADR-0018-constitutional-first-principles.md`; `ADR-0019-executive-governance.md`; `CONST-0001` | `docs/constitution/executive.md`; `docs/constitution/architecture_principles.md`; `docs/architecture/00_JARVIS_ARCHITECTURE.md` | Constitutional document-integrity verification and Article-level traceability certification are required | Constitution, Executive public package, governance metadata, constitutional fingerprint | Establishes constitutional supremacy, governing hierarchy, continuity, and interpretation | **Partial** — doctrine exists; automated supremacy and cross-reference enforcement remain Pending G2 |
| **II — Purpose of the Executive** | `core/executive`; `core/cognition` | `WP-0011`; `ADR-0019-executive-governance.md`; `ADR-0020-genesis-iv-cognition-architecture-constitution.md` | `docs/architecture/11_cognitive_architecture.md`; `docs/architecture/gen2_mission_engine.md`; `docs/constitution/executive.md` | Genesis VI cognition regressions; Executive integration audit; future Article II constitutional verification | Executive Director, mission engine, cognition cycle, session and operations projection APIs | Transforms observation into understanding, reasoning, decision, planning, execution, and reporting | **Mapped** — core executive and cognition foundations exist; full end-to-end constitutional certification remains Pending G2 |
| **III — Authority and Delegation** | `core/executive`; mission and executive-session authority boundaries | `ADR-0019-executive-governance.md`; `ADR-0031` Executive Decision Boundary | `docs/constitution/executive.md`; `docs/specifications/decisions_episode.md`; `docs/specifications/execution_contract.md` | Genesis VI executive-session and cognition-cycle verification; delegated-authority certification required | Executive session, mission ownership, decision records, authorization and revocation contracts | Defines Commander authority, delegation scope, accountability, attribution, and revocation | **Partial** — authority concepts exist; explicit delegation registry and revocation enforcement remain Pending G2 |
| **IV — Separation of Powers** | `core/evidence`; `core/reasoning`; `core/cognition`; `core/executive`; execution and oversight boundaries | `ADR-0020-genesis-iv-cognition-architecture-constitution.md`; `ADR-0021-cognitive-object-model.md`; `ADR-0019-executive-governance.md` | `docs/architecture/11_cognitive_architecture.md`; `docs/architecture/12_reasoning_architecture.md`; `docs/architecture/subsystem_ownership.md` | Cognitive-ownership migration audit; package-isolation tests; public-API compatibility verification; Genesis IV and VI regressions | Observation, evidence, reasoning, cognition, decision, planning, execution, and oversight modules | Prevents unrestricted concentration of observation, reasoning, authorization, execution, and certification | **Mapped** — subsystem separation exists and is independently testable; continuous boundary monitoring remains Pending G2 |
| **V — Evidence Doctrine** | `core/evidence` | `ADR-0018-genesis-iv-evidence-constitution.md`; `ADR-0019-canonical-evidence-model.md`; `ADR-0019-genesis-iv-claim-constitution.md` | Evidence Constitution; canonical evidence architecture; cognitive-ownership migration map | `tests/test_genesis_4r3a_pack1_evidence_foundation.py`; Pack 2A domain-contract tests; Genesis IV-R3A certification suites | `core/evidence/enums.py`; `errors.py`; `observation.py`; evidence assessment, admissibility, proposition, source-reference and serialization APIs | Preserves admissible, immutable, attributable, contradictory, and sufficiency-rated evidence | **Mapped** — canonical evidence ownership and verification exist |
| **VI — Truthfulness** | `core/evidence`; `core/reasoning`; Executive response and provenance surfaces | `WP-0011`; `ADR-0030` Executive Reasoning Policy; evidence and cognition ADRs | `docs/constitution/reasoning.md`; `docs/specifications/reasoning_contract.md`; `docs/architecture/reasoning_engine_foundation.md` | Reasoning foundation tests; evidence provenance tests; deterministic inference fixtures; future truth-classification verifier | Observation/evidence/inference distinctions, assumptions, confidence, provenance, error records and reasoning outputs | Distinguishes fact, observation, evidence, inference, assumption, estimate, recommendation, and decision | **Partial** — supporting data models exist; universal output-level truth classification remains Pending G2 |
| **VII — Uncertainty** | `core/reasoning`; `core/evidence`; cognition working memory | `WP-0011`; `ADR-0030` Executive Reasoning Policy | `docs/architecture/reasoning_engine_foundation.md`; `docs/architecture/reasoning_hypothesis_knowledge_integration.md`; `docs/specifications/reasoning_contract.md` | `dev/verify_phase_x.sh`; `dev/verify_phase_xb.sh`; deterministic reasoning and hypothesis-selection tests | Confidence model, uncertainty representation, hypothesis generation, knowledge evidence adapter and reasoning pipeline | Represents confidence, unknowns, conflicting evidence, abstention conditions, and revision | **Mapped** — confidence and hypothesis infrastructure exists; calibrated operational thresholds remain a future policy layer |
| **VIII — Executive Judgment** | `core/reasoning`; `core/cognition`; `core/executive` | `WP-0011`; `WP-0012`; `ADR-0030` Executive Reasoning Policy | `docs/architecture/12_reasoning_architecture.md`; reasoning foundation and hypothesis-integration architecture | Phase X/X-B verification; Genesis VI cognition-cycle regressions; future judgment-record certification | Inference engine, hypothesis generator, evidence adapter, reasoning pipeline, cognition cycle and recommendation projection | Produces reasoned, reviewable, evidence-supported recommendations with confidence and uncertainty | **Mapped** — deterministic reasoning foundation exists; formal constitutional judgment object may require consolidation |
| **IX — Course-of-Action Evaluation** | `core/reasoning`; Executive evaluation policy | `WP-0012`; `ADR-0032` Executive Course-of-Action Generation; `ADR-0033` Executive Course-of-Action Evaluation | Executive decision-theory architecture; reasoning and decision specifications | Deterministic Course-of-Action generation and scoring verification required; hard-constraint and abstention certification required | Candidate generation, policy evaluation, constraint filtering, scoring, comparison, tie resolution and recommendation records | Generates, filters, compares and ranks constitutionally admissible Courses of Action | **Partial** — governing doctrine exists; complete Article IX enforcement and certification remain Pending G2 |
| **X — Executive Decision** | `core/executive`; `core/cognition`; decision boundary | `WP-0012`; `ADR-0031` Executive Decision Boundary | `docs/specifications/decisions_episode.md`; Executive session and cognition-cycle architecture | Genesis VI-A1 through A6 regressions; executive-session tests; checkpoint and integrity certification | Decision record, approving authority, executive session, cognition cycle, checkpoint store and public executive APIs | Converts an authorized recommendation into a permanent, attributable commitment | **Mapped** — session, state, checkpoint and integrity foundations exist; explicit human/delegated approval enforcement remains Pending G2 |
| **XI — Executive Planning** | `core/executive.planning`; mission engine and mission compiler | Planning Constitution; applicable mission-engine ADRs | `docs/architecture/13_mission_planning_architecture.md`; `docs/specifications/planning_contract.md`; `docs/architecture/gen2_mission_engine.md` | Gen 2 Mission Engine and capability-routing verification; plan-contract and mission-compiler tests; pre-execution certification required | Mission, Objective, Task, Activity, planner, dependency, contingency, resource and success-criteria APIs | Transforms authorized decisions into verified missions, objectives, tasks and activities | **Mapped** — mission-planning foundations exist; comprehensive constitutional pre-execution verification remains Pending G2 |
| **XII — Executive Execution** | Execution subsystem; `core/executive`; operations routes and activity lifecycle | Execution Constitution; Executive governance and decision-boundary ADRs | `docs/constitution/execution.md`; `docs/specifications/execution_contract.md`; operations architecture | Execution-contract verification; mission-lifecycle regressions; authorization and safe-suspension certification required | Execution activities, command dispatch, operations route, timeline, status transitions, completion and recovery records | Performs only authorized work while preserving intent, observation, suspension and completion evidence | **Partial** — operational projections and contracts exist; full execution authority gate remains Pending G2 |
| **XIII — Safety** | Executive governance, execution subsystem, integrity engine and Commander oversight | Constitutional first principles; Executive governance ADR; future dedicated safety-policy ADR | `docs/constitution/executive.md`; `docs/constitution/execution.md`; engineering and operational standards | Genesis VI-A6.4 integrity verification; failure, rollback, suspension and degraded-mode tests; safety certification required | Integrity engine, execution suspension, revocation, rollback, containment, escalation and recovery interfaces | Prioritizes human safety, constitutional authority, mission integrity, assets and information integrity | **Partial** — integrity and suspension foundations exist; unified constitutional safety policy engine remains Pending G2 |
| **XIV — Transparency** | `core/evidence`; `core/executive`; operations API; executive integration and UI projection layers | `ADR-0017-progressive-workspace-tools.md`; `ADR-EXEC-0001-canonical-integration-plane.md`; evidence and governance ADRs | `docs/architecture/executive_projection_contract.md`; `executive_integration_architecture.md`; `capability_visibility_contract.md`; Mission Control UI architecture | Executive integration audit; Genesis VI-A2 Executive Mission Control verification; provenance and lineage tests | `/operations/executive`; mission workspace; Commander Brief; timeline; evidence provenance; status, health and constitutional projections | Makes mission state, evidence, reasoning, confidence, authority, progress and system limitations visible | **Mapped** — executive and UI transparency surfaces exist; end-to-end Article XIV lineage certification remains Pending G2 |
| **XV — Determinism** | Engineering OS; `core/cognition`; serialization, checkpoint and integrity subsystems | Engineering Constitution; cognition architecture ADR; canonical evidence ADR | `docs/engineering/engineering_os_architecture.md`; canonical snapshot and repository-integrity architecture | Genesis V-E0, V-E1A and V-E1B verification; public-API compatibility report; Genesis VI-A6.2, A6.3 and A6.4 certification | Canonical serializers, stable fingerprints, checkpoint store, integrity engine, deterministic reasoning fixtures and regression framework | Produces reproducible artifacts and detects architectural or behavioral drift | **Mapped** — deterministic fingerprints, compatibility verification, checkpoints and integrity certification exist |
| **XVI — Institutional Memory** | Working-memory, executive-session, checkpoint, knowledge and operational-memory subsystems | `ADR-0018-operational-memory.md`; knowledge lifecycle and canonical knowledge ADRs | `docs/architecture/memory_engine.md`; `docs/constitution/memory.md`; knowledge lifecycle architecture | Genesis VI-A2 Working Memory, VI-A5 Executive Session and VI-A6.3 Checkpoint Store verification; knowledge lifecycle regressions | Working memory, session history, canonical snapshots, checkpoint repository, knowledge catalog and mission-history records | Preserves operational, mission, decision, engineering, knowledge and constitutional history | **Mapped** — memory and checkpoint foundations exist; structured lessons-learned admission policy remains incomplete |
| **XVII — Constitutional Governance and Amendment** | Commander; `docs/constitution`; `docs/decisions`; engineering certification authority | `ADR-0018-constitutional-first-principles.md`; `ADR-0019-executive-governance.md`; future amendment-process ADR | `docs/constitution/executive.md`; ADR template and repository governance standards | Constitutional fingerprint, cross-reference validation, amendment-impact verification and ratification certification required | Constitution revision metadata, archived versions, ADR records, migration plans and certification reports | Controls amendment, compatibility, stewardship, historical preservation and constitutional evolution | **Partial** — doctrine is complete; automated amendment workflow and ratification gate remain Pending G2 |
| **XVIII — Normative Requirements** | Engineering OS; repository verification framework; package owners | Engineering Constitution; architecture and ownership ADRs; constitutional first principles | `docs/constitution/ENGINEERING_CONSTITUTION.md`; `docs/engineering/JARVIS_ENGINEERING_STANDARD.md`; `docs/architecture/subsystem_ownership.md`; `docs/glossary.md` | Genesis V certification; public-API compatibility verification; architecture fingerprinting; repository-integrity verification | Verification registry, engineering CLI, ownership maps, canonical glossary, package exports and repository standards | Enforces normative language, governance-before-implementation, canonical terminology and repository authority | **Mapped** — engineering verification system exists; direct Article XVIII compliance report remains Pending G2 |
| **XIX — Constitutional Compliance** | Future `core/governance` or `core/compliance`; `dev/verification`; audits and certification authority | `CONST-0001`; constitutional governance ADR; proposed Genesis IV-G2 Constitutional Enforcement ADR | Constitutional Compliance architecture; traceability schema; certification and violation-management specifications | Constitutional Registry verification; Article Registry verification; traceability audit; violation classification; remediation and certification suites | Constitutional Registry, Article Registry, Compliance Engine, Traceability Engine, certification records, audit records and governance dashboard | Determines, records, monitors and demonstrates constitutional compliance across the full Executive Operating System | **Pending G2** — Article XIX defines the requirements for the next Constitutional Enforcement Engine phase |

Every Article shall map to responsible packages, ADRs, verification suites,

certification suites, and implementation modules.
"""

# Remove blank space between the lifecycle and the original paragraph.
before = text[:insert_start].rstrip()
after = text[next_section_index:]

updated = before + matrix + "\n\n" + after

path.write_text(updated, encoding="utf-8")

print("[PASS] Populated Constitutional Compliance Matrix inserted.")
PY

echo
echo "------------------------------------------------------------------------"
echo "Verifying installation..."
echo "------------------------------------------------------------------------"

CONSTITUTION_PATH="${CONSTITUTION}" python3 <<'PY'
from __future__ import annotations

import os
import re
from pathlib import Path


path = Path(os.environ["CONSTITUTION_PATH"])
text = path.read_text(encoding="utf-8")

required_fragments = (
    "## Constitutional Compliance Matrix",
    "**I — Constitutional Authority**",
    "**V — Evidence Doctrine**",
    "**X — Executive Decision**",
    "**XV — Determinism**",
    "**XIX — Constitutional Compliance**",
    "Observation → Verification → Certification → Operational Learning",
    "Every Article shall map to responsible packages, ADRs, verification suites,",
)

missing = [fragment for fragment in required_fragments if fragment not in text]

if missing:
    print("[FAIL] Required matrix content is missing:")
    for item in missing:
        print(f"       - {item}")
    raise SystemExit(1)

matrix_start = text.index("## Constitutional Compliance Matrix")
following_text = text[matrix_start:]

article_rows = re.findall(
    r"^\| \*\*(?:I|II|III|IV|V|VI|VII|VIII|IX|X|XI|XII|XIII|XIV|XV|XVI|XVII|XVIII|XIX) —",
    following_text,
    flags=re.MULTILINE,
)

if len(article_rows) != 19:
    raise SystemExit(
        f"[FAIL] Expected 19 Constitutional Article rows; found {len(article_rows)}."
    )

lifecycle_position = text.index(
    "Observation → Verification → Certification → Operational Learning"
)
matrix_position = text.index("## Constitutional Compliance Matrix")
article_mapping_position = text.index(
    "Every Article shall map to responsible packages, ADRs, verification suites,",
    matrix_position,
)

if not lifecycle_position < matrix_position < article_mapping_position:
    raise SystemExit(
        "[FAIL] Matrix is not positioned between Operational Learning "
        "and the Article-mapping paragraph."
    )

print("[PASS] Matrix heading present.")
print("[PASS] All 19 Constitutional Articles are represented.")
print("[PASS] Matrix is positioned after Operational Learning.")
print("[PASS] Matrix is positioned before the Article-mapping paragraph.")
print("[PASS] Constitution remains readable as UTF-8.")
PY

echo
echo "------------------------------------------------------------------------"
echo "[PASS] CONST-0001 Constitutional Compliance Matrix installed"
echo "------------------------------------------------------------------------"
echo
echo "Constitution:"
echo "  ${CONSTITUTION}"
echo
echo "Backup:"
echo "  ${BACKUP_FILE}"
echo
echo "Review command:"
echo "  sed -n '/Constitutional Compliance Matrix/,/ARTICLE I/p' \\"
echo "      '${CONSTITUTION}' | less"
echo
echo "========================================================================"
