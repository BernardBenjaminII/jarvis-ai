from __future__ import annotations

from pathlib import Path
import sys


def _bootstrap_certification_runtime() -> Path:
    current = Path(__file__).resolve()

    for candidate in (current.parent, *current.parents):
        if all(
            (candidate / name).is_dir()
            for name in ("core", "dev", "docs")
        ):
            candidate_text = str(candidate)
            if candidate_text not in sys.path:
                sys.path.insert(0, candidate_text)
            return candidate

    raise RuntimeError("Unable to locate the JARVIS project root.")


PROJECT_ROOT = _bootstrap_certification_runtime()


import argparse
import inspect
import json
import sqlite3
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class CertificationCheck:
    code: str
    label: str
    status: str
    expected: Any
    actual: Any
    detail: str

    @property
    def passed(self) -> bool:
        return self.status == "PASS"


def object_identity(value: Any) -> dict[str, Any] | None:
    if value is None:
        return None
    return {
        "type": type(value).__name__,
        "module": type(value).__module__,
        "qualified_type": f"{type(value).__module__}.{type(value).__name__}",
    }


def callable_identity(value: Any) -> dict[str, Any] | None:
    if value is None:
        return None

    return {
        "name": getattr(value, "__name__", type(value).__name__),
        "qualname": getattr(value, "__qualname__", type(value).__qualname__),
        "module": getattr(value, "__module__", type(value).__module__),
        "signature": str(inspect.signature(value)) if callable(value) else None,
        "bound_owner": (
            object_identity(getattr(value, "__self__", None))
            if getattr(value, "__self__", None) is not None
            else None
        ),
    }


def check(
    code: str,
    label: str,
    *,
    expected: Any,
    actual: Any,
    detail: str,
) -> CertificationCheck:
    return CertificationCheck(
        code=code,
        label=label,
        status="PASS" if actual == expected else "FAIL",
        expected=expected,
        actual=actual,
        detail=detail,
    )


def check_true(
    code: str,
    label: str,
    *,
    actual: bool,
    detail: str,
) -> CertificationCheck:
    return check(
        code,
        label,
        expected=True,
        actual=bool(actual),
        detail=detail,
    )


def inspect_database(path: Path) -> dict[str, Any]:
    result: dict[str, Any] = {
        "path": str(path),
        "exists": path.is_file(),
        "tables": {},
    }
    if not path.is_file():
        return result

    with sqlite3.connect(path) as conn:
        for table in (
            "catalog_documents",
            "document_subjects",
            "runtime_documents",
            "runtime_chunks",
            "runtime_chunks_fts",
            "chunk_embeddings",
        ):
            exists = conn.execute(
                """
                SELECT 1
                FROM sqlite_master
                WHERE name=?
                  AND type IN ('table', 'view')
                """,
                (table,),
            ).fetchone() is not None

            count = None
            if exists:
                try:
                    count = int(
                        conn.execute(
                            f'SELECT COUNT(*) FROM "{table}"'
                        ).fetchone()[0]
                    )
                except sqlite3.Error:
                    count = None

            result["tables"][table] = {
                "exists": exists,
                "row_count": count,
            }

    return result


def runtime_snapshot() -> dict[str, Any]:
    from core.src.routes.api import conversation_service
    from core.conversation.orchestrator import ExecutiveConversationOrchestrator
    from core.conversation.grounding import CatalogGroundingService
    from core.knowledge_awareness.service import (
        ExecutiveKnowledgeAwarenessService,
    )
    from core.executive.director import ExecutiveDirector
    from core.conversation.service import ExecutiveConversationService
    from core.conversation.compiler import ExecutiveRequestCompiler
    from core.conversation.repository import ConversationRepository
    from core.knowledge_catalog.search import search_catalog
    from core.knowledge_catalog.materialization.search import (
        search_runtime_knowledge,
    )

    orchestrator = conversation_service.orchestrator
    grounding_service = (
        getattr(orchestrator, "grounding_service", None)
        if orchestrator is not None
        else None
    )

    snapshot = {
        "conversation_service": object_identity(conversation_service),
        "compiler": object_identity(
            getattr(conversation_service, "compiler", None)
        ),
        "repository": object_identity(
            getattr(conversation_service, "repository", None)
        ),
        "orchestrator": object_identity(orchestrator),
        "answer_handler": callable_identity(
            getattr(conversation_service, "answer_handler", None)
        ),
        "grounding_service": object_identity(grounding_service),
        "awareness_service": object_identity(
            getattr(orchestrator, "awareness_service", None)
            if orchestrator is not None
            else None
        ),
        "director": object_identity(
            getattr(orchestrator, "director", None)
            if orchestrator is not None
            else None
        ),
        "observability_service": object_identity(
            getattr(orchestrator, "observability_service", None)
            if orchestrator is not None
            else None
        ),
        "synthesis_handler": callable_identity(
            getattr(orchestrator, "synthesis_handler", None)
            if orchestrator is not None
            else None
        ),
        "grounding_search_handler": callable_identity(
            getattr(grounding_service, "search_handler", None)
            if grounding_service is not None
            else None
        ),
        "catalog_database": (
            str(getattr(grounding_service, "database_path", ""))
            if grounding_service is not None
            else None
        ),
        "conversation_ask": callable_identity(
            getattr(conversation_service, "ask", None)
        ),
        "canonical_search": callable_identity(search_catalog),
        "runtime_search": callable_identity(search_runtime_knowledge),
        "expected_types": {
            "conversation_service": object_identity(
                ExecutiveConversationService
            ),
            "compiler": object_identity(ExecutiveRequestCompiler),
            "repository": object_identity(ConversationRepository),
            "orchestrator": object_identity(
                ExecutiveConversationOrchestrator
            ),
            "grounding_service": object_identity(
                CatalogGroundingService
            ),
            "awareness_service": object_identity(
                ExecutiveKnowledgeAwarenessService
            ),
            "director": object_identity(ExecutiveDirector),
        },
    }

    database_path = Path(snapshot["catalog_database"] or "")
    snapshot["database"] = inspect_database(database_path)

    return snapshot


def source_contract_checks(root: Path) -> list[CertificationCheck]:
    orchestrator_path = root / "core/conversation/orchestrator.py"
    catalog_search_path = root / "core/knowledge_catalog/search.py"
    runtime_search_path = (
        root / "core/knowledge_catalog/materialization/search.py"
    )

    orchestrator_source = orchestrator_path.read_text(
        encoding="utf-8",
        errors="replace",
    )
    catalog_source = catalog_search_path.read_text(
        encoding="utf-8",
        errors="replace",
    )
    runtime_source = runtime_search_path.read_text(
        encoding="utf-8",
        errors="replace",
    )

    return [
        check_true(
            "SOURCE-GROUND",
            "Orchestrator calls grounding service",
            actual=(
                "self.grounding_service.ground(context)"
                in orchestrator_source
            ),
            detail=(
                "The canonical orchestrator must invoke grounding before "
                "answer synthesis."
            ),
        ),
        check_true(
            "SOURCE-AWARENESS",
            "Orchestrator assesses grounding",
            actual=(
                "self.awareness_service.assess(grounding)"
                in orchestrator_source
            ),
            detail=(
                "Knowledge awareness must consume the GroundingResult."
            ),
        ),
        check_true(
            "SOURCE-GROUNDING-SYNTHESIS",
            "Grounding contributes to synthesis input",
            actual=(
                "grounding.synthesis_input(synthesis_input)"
                in orchestrator_source
            ),
            detail=(
                "Retrieved evidence must be added to the synthesis prompt."
            ),
        ),
        check_true(
            "SOURCE-AWARENESS-SYNTHESIS",
            "Knowledge state contributes to synthesis input",
            actual=(
                "knowledge_state.synthesis_input(synthesis_input)"
                in orchestrator_source
            ),
            detail=(
                "Knowledge awareness state must influence synthesis."
            ),
        ),
        check_true(
            "SOURCE-SYNTHESIS-HANDLER",
            "Orchestrator invokes synthesis handler",
            actual="self.synthesis_handler(" in orchestrator_source,
            detail=(
                "The grounded prompt must reach the configured synthesis "
                "handler."
            ),
        ),
        check_true(
            "SOURCE-CANONICAL-DELEGATION",
            "Canonical search delegates to runtime search",
            actual="search_runtime_knowledge(" in catalog_source,
            detail=(
                "core.knowledge_catalog.search.search_catalog must use "
                "runtime materialized retrieval."
            ),
        ),
        check_true(
            "SOURCE-FTS",
            "Runtime search uses FTS",
            actual=(
                "runtime_chunks_fts" in runtime_source
                and "MATCH" in runtime_source
            ),
            detail=(
                "Mark I retrieval must use the certified SQLite FTS path."
            ),
        ),
    ]


def runtime_checks(snapshot: dict[str, Any]) -> list[CertificationCheck]:
    checks: list[CertificationCheck] = []

    expected = {
        "conversation_service":
            "core.conversation.service.ExecutiveConversationService",
        "compiler":
            "core.conversation.compiler.ExecutiveRequestCompiler",
        "repository":
            "core.conversation.repository.ConversationRepository",
        "orchestrator":
            "core.conversation.orchestrator.ExecutiveConversationOrchestrator",
        "grounding_service":
            "core.conversation.grounding.CatalogGroundingService",
        "awareness_service":
            (
                "core.knowledge_awareness.service."
                "ExecutiveKnowledgeAwarenessService"
            ),
        "director":
            "core.executive.director.ExecutiveDirector",
    }

    for key, qualified in expected.items():
        actual = (
            snapshot.get(key, {}) or {}
        ).get("qualified_type")
        checks.append(
            check(
                f"RUNTIME-{key.upper()}",
                f"Live {key.replace('_', ' ')} identity",
                expected=qualified,
                actual=actual,
                detail=(
                    "Certification uses exact module and class identity, "
                    "not class-name matching."
                ),
            )
        )

    checks.append(
        check(
            "RUNTIME-LEGACY-BYPASS",
            "Legacy answer handler is disabled",
            expected=None,
            actual=snapshot.get("answer_handler"),
            detail=(
                "The Executive conversation service must use the "
                "orchestrator rather than the legacy answer handler."
            ),
        )
    )

    search_handler = snapshot.get("grounding_search_handler") or {}
    checks.append(
        check(
            "RUNTIME-SEARCH-HANDLER",
            "Grounding uses its canonical search handler",
            expected=(
                "CatalogGroundingService._search_catalog"
            ),
            actual=search_handler.get("qualname"),
            detail=(
                "The live grounding service must delegate through its "
                "canonical catalog-search adapter."
            ),
        )
    )

    canonical_search = snapshot.get("canonical_search") or {}
    runtime_search = snapshot.get("runtime_search") or {}

    checks.extend(
        [
            check(
                "RUNTIME-CANONICAL-SEARCH",
                "Canonical search function identity",
                expected=(
                    "core.knowledge_catalog.search.search_catalog"
                ),
                actual=(
                    f"{canonical_search.get('module')}."
                    f"{canonical_search.get('qualname')}"
                ),
                detail=(
                    "The imported catalog search function must be the "
                    "canonical production implementation."
                ),
            ),
            check(
                "RUNTIME-MATERIALIZED-SEARCH",
                "Runtime search function identity",
                expected=(
                    "core.knowledge_catalog.materialization.search."
                    "search_runtime_knowledge"
                ),
                actual=(
                    f"{runtime_search.get('module')}."
                    f"{runtime_search.get('qualname')}"
                ),
                detail=(
                    "Runtime retrieval must resolve to IX-A3 materialized "
                    "knowledge search."
                ),
            ),
        ]
    )

    synthesis = snapshot.get("synthesis_handler") or {}
    checks.append(
        check_true(
            "RUNTIME-SYNTHESIS",
            "Synthesis handler is callable",
            actual=bool(synthesis.get("signature")),
            detail=(
                "A callable synthesis endpoint must be injected into the "
                "orchestrator."
            ),
        )
    )

    database = snapshot.get("database") or {}
    checks.append(
        check_true(
            "RUNTIME-DATABASE",
            "Catalog database exists",
            actual=bool(database.get("exists")),
            detail=(
                "The live grounding service database path must resolve to "
                "an existing SQLite file."
            ),
        )
    )

    tables = database.get("tables") or {}
    for table in (
        "runtime_documents",
        "runtime_chunks",
        "runtime_chunks_fts",
    ):
        checks.append(
            check_true(
                f"RUNTIME-TABLE-{table.upper()}",
                f"{table} is present and populated",
                actual=bool(
                    (tables.get(table) or {}).get("exists")
                    and ((tables.get(table) or {}).get("row_count") or 0) > 0
                ),
                detail=(
                    "The live Mark I retrieval corpus must contain "
                    f"populated {table}."
                ),
            )
        )

    return checks


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Genesis IX-A4.1B Pack 3A — Executive Runtime Certification",
        "",
        f"**Generated:** {report['generated_at']}",
        f"**Repository:** `{report['repository_root']}`",
        f"**Overall status:** **{report['overall_status']}**",
        "",
        "## Certification Summary",
        "",
        f"- Checks executed: **{report['checks_executed']}**",
        f"- Checks passed: **{report['checks_passed']}**",
        f"- Checks failed: **{report['checks_failed']}**",
        "",
        "## Certified Runtime Chain",
        "",
        "```text",
        "ExecutiveConversationService",
        "    ↓",
        "ExecutiveRequestCompiler",
        "    ↓",
        "ExecutiveConversationOrchestrator",
        "    ↓",
        "CatalogGroundingService",
        "    ↓",
        "core.knowledge_catalog.search.search_catalog",
        "    ↓",
        "search_runtime_knowledge",
        "    ↓",
        "runtime_chunks_fts",
        "    ↓",
        "GroundingResult",
        "    ↓",
        "ExecutiveKnowledgeAwarenessService",
        "    ↓",
        "ExecutiveDirector",
        "    ↓",
        "synthesis_handler",
        "```",
        "",
        "## Checks",
        "",
        "| Code | Check | Status | Expected | Actual |",
        "|---|---|---|---|---|",
    ]

    for item in report["checks"]:
        lines.append(
            f"| `{item['code']}` | {item['label']} | "
            f"**{item['status']}** | "
            f"`{item['expected']}` | `{item['actual']}` |"
        )

    lines.extend(
        [
            "",
            "## Live Snapshot",
            "",
            "```json",
            json.dumps(report["runtime_snapshot"], indent=2, sort_keys=True),
            "```",
            "",
            "## Constitutional Result",
            "",
        ]
    )

    if report["overall_status"] == "EXCELLENT":
        lines.append(
            "The Executive runtime uses one certified conversation and "
            "retrieval chain. No legacy answer-handler bypass is active."
        )
    else:
        lines.append(
            "Certification failed. Runtime retrieval ownership must be "
            "repaired before Pack 3B trace certification proceeds."
        )

    return "\n".join(lines)


def certify(root: Path) -> dict[str, Any]:
    snapshot = runtime_snapshot()
    checks = [
        *runtime_checks(snapshot),
        *source_contract_checks(root),
    ]

    passed = sum(1 for item in checks if item.passed)
    failed = len(checks) - passed

    return {
        "schema_version": "genesis_ix_a4_1b_pack3a_v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "repository_root": str(root),
        "overall_status": "EXCELLENT" if failed == 0 else "FAILED",
        "checks_executed": len(checks),
        "checks_passed": passed,
        "checks_failed": failed,
        "checks": [asdict(item) for item in checks],
        "runtime_snapshot": snapshot,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Genesis IX-A4.1B Pack 3A Executive Runtime Certification"
        )
    )
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(
            "docs/audits/genesis_ix_a4_1b_pack3a"
        ),
    )
    args = parser.parse_args()

    root = args.root.resolve()
    output = args.output_dir
    if not output.is_absolute():
        output = root / output
    output.mkdir(parents=True, exist_ok=True)

    report = certify(root)

    (output / "executive_runtime_certification.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output / "executive_runtime_certification.md").write_text(
        render_markdown(report) + "\n",
        encoding="utf-8",
    )

    print("=" * 76)
    print("GENESIS IX-A4.1B PACK 3A — EXECUTIVE RUNTIME CERTIFICATION")
    print("=" * 76)
    print("Checks executed :", report["checks_executed"])
    print("Checks passed   :", report["checks_passed"])
    print("Checks failed   :", report["checks_failed"])
    print("Overall status  :", report["overall_status"])
    print("Output          :", output)
    print("=" * 76)

    return 0 if report["overall_status"] == "EXCELLENT" else 1


if __name__ == "__main__":
    raise SystemExit(main())
