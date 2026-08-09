from __future__ import annotations

import inspect
import inspect
import json
import re
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterator, Mapping

from .contracts import CertificationCheck, EndToEndCertificationReport


WORD_RE = re.compile(r"[A-Za-z][A-Za-z0-9_./+-]*")
HEX_RE = re.compile(r"^[0-9a-fA-F]{24,}$")
METADATA_TERMS = frozenset(
    {
        "sha256", "metadata", "document", "documents", "file",
        "file_path", "path", "confidence", "score", "chunk",
        "chunk_id", "document_id", "created_at", "updated_at",
        "assigned_by", "content", "text", "source", "runtime",
        "catalog", "page", "chapter", "http", "https",
    }
)


def mapping(value: Any) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return dict(value)
    if hasattr(value, "to_dict") and callable(value.to_dict):
        result = value.to_dict()
        if isinstance(result, Mapping):
            return dict(result)
    return {}


def check(
    code: str,
    label: str,
    condition: bool,
    detail: str,
    *,
    expected: Any = True,
    actual: Any = None,
) -> CertificationCheck:
    return CertificationCheck(
        code=code,
        label=label,
        status="PASS" if condition else "FAIL",
        detail=detail,
        expected=expected,
        actual=actual if actual is not None else condition,
    )


class EndToEndRetrievalTracer:
    def __init__(
        self,
        *,
        repository_root: Path,
        catalog_database: Path | None,
    ) -> None:
        self.repository_root = repository_root.resolve()
        self.catalog_database = (
            catalog_database.resolve()
            if catalog_database is not None
            else None
        )

    def certify(
        self,
        *,
        gap_query: str = (
            "internal architecture of the Quantum Banana Warp Core Mk XII"
        ),
    ) -> EndToEndCertificationReport:
        from core.src.routes.api import conversation_service
        from core.knowledge_catalog.qualified_search import search_qualified_catalog as search_catalog

        orchestrator = conversation_service.orchestrator
        grounding = getattr(orchestrator, "grounding_service", None)
        awareness = getattr(orchestrator, "awareness_service", None)
        director = getattr(orchestrator, "director", None)

        runtime_snapshot = {
            "conversation_service": self._identity(conversation_service),
            "orchestrator": self._identity(orchestrator),
            "grounding_service": self._identity(grounding),
            "awareness_service": self._identity(awareness),
            "director": self._identity(director),
            "synthesis_handler": self._callable_identity(
                getattr(orchestrator, "synthesis_handler", None)
            ),
            "catalog_database": (
                str(getattr(grounding, "database_path", ""))
                if grounding is not None
                else None
            ),
            "search_handler": self._callable_identity(
                getattr(grounding, "search_handler", None)
                if grounding is not None
                else None
            ),
        }

        checks: list[CertificationCheck] = [
            check(
                "RUNTIME-CONVERSATION",
                "Conversation service is live",
                conversation_service is not None,
                "The canonical conversation service must be importable.",
            ),
            check(
                "RUNTIME-ORCHESTRATOR",
                "Executive orchestrator is live",
                orchestrator is not None,
                "The conversation service must own an orchestrator.",
            ),
            check(
                "RUNTIME-GROUNDING",
                "Grounding service is live",
                grounding is not None,
                "The orchestrator must own CatalogGroundingService.",
            ),
            check(
                "RUNTIME-AWARENESS",
                "Knowledge awareness is live",
                awareness is not None,
                "The orchestrator must own knowledge awareness.",
            ),
            check(
                "RUNTIME-DIRECTOR",
                "Executive Director is live",
                director is not None,
                "The orchestrator must own ExecutiveDirector.",
            ),
        ]

        known_query = self._discover_known_query(search_catalog)
        checks.append(
            check(
                "KNOWN-QUERY",
                "Known catalog query discovered",
                bool(known_query),
                "Certification must derive a real query from the live corpus.",
                expected="non-empty query",
                actual=known_query,
            )
        )

        known_trace: dict[str, Any] = {}
        if known_query:
            known_trace = self._run_request(
                conversation_service,
                orchestrator,
                known_query,
                expected_gap=False,
            )
            checks.extend(self._known_checks(known_trace))

        gap_trace = self._run_request(
            conversation_service,
            orchestrator,
            gap_query,
            expected_gap=True,
        )
        checks.extend(self._gap_checks(gap_trace))

        checks.extend(self._source_contract_checks())

        return EndToEndCertificationReport(
            schema_version="genesis_ix_a4_3_v1",
            generated_at=datetime.now(timezone.utc).isoformat(),
            repository_root=str(self.repository_root),
            catalog_database=(
                str(self.catalog_database)
                if self.catalog_database is not None
                else None
            ),
            known_query=known_query,
            gap_query=gap_query,
            checks=tuple(checks),
            known_trace=known_trace,
            gap_trace=gap_trace,
            runtime_snapshot=runtime_snapshot,
        )

    def _discover_known_query(
        self,
        search_catalog: Callable[..., Any],
    ) -> str | None:
        candidates = self._database_terms()

        for candidate in candidates:
            try:
                rows = list(
                    search_catalog(
                        candidate,
                        db_path=self.catalog_database,
                        limit=8,
                    )
                )
            except TypeError:
                rows = list(search_catalog(candidate, limit=8))
            except Exception:
                continue

            if rows:
                return candidate

        return None

    def _database_terms(self) -> list[str]:
        """Return deterministic semantic phrases from the live corpus."""
        if self.catalog_database is None or not self.catalog_database.is_file():
            return []

        candidates: list[str] = []
        seen: set[str] = set()

        def add_candidate(value: Any) -> None:
            phrase = self._semantic_phrase(str(value or ""))
            key = phrase.casefold()
            if not phrase or key in seen:
                return
            seen.add(key)
            candidates.append(phrase)

        with sqlite3.connect(self.catalog_database) as connection:
            tables = {
                str(row[0])
                for row in connection.execute(
                    "SELECT name FROM sqlite_master "
                    "WHERE type IN ('table','view')"
                ).fetchall()
            }

            probes = [
                ("runtime_documents", ("title",)),
                ("catalog_documents", ("title",)),
                ("document_subjects", ("subject",)),
                ("knowledge_registry", ("title", "subject")),
                ("runtime_chunks", ("chunk_text", "text", "content")),
            ]

            for table, possible_columns in probes:
                if table not in tables:
                    continue

                columns = {
                    str(row[1])
                    for row in connection.execute(
                        f'PRAGMA table_info("{table}")'
                    ).fetchall()
                }

                for column in possible_columns:
                    if column not in columns:
                        continue

                    try:
                        rows = connection.execute(
                            f'SELECT "{column}" FROM "{table}" '
                            f'WHERE "{column}" IS NOT NULL '
                            f'AND length(trim("{column}")) >= 8 '
                            f'LIMIT 300'
                        ).fetchall()
                    except sqlite3.Error:
                        continue

                    for row in rows:
                        add_candidate(row[0])
                        if len(candidates) >= 250:
                            return candidates

        return candidates

    @staticmethod
    def _semantic_phrase(value: str) -> str:
        """Normalize one corpus value into a meaningful multi-word query."""
        words: list[str] = []

        for token in WORD_RE.findall(value):
            lowered = token.casefold()
            if lowered in METADATA_TERMS:
                continue
            if HEX_RE.fullmatch(token):
                continue
            if token.startswith(("http://", "https://")):
                continue
            words.append(token)
            if len(words) >= 10:
                break

        if len(words) < 2:
            return ""

        phrase = " ".join(words).strip()
        if len(phrase) < 8:
            return ""
        if not any(len(word) >= 5 for word in words):
            return ""
        return phrase

    @contextmanager
    def _capture_synthesis(
        self,
        orchestrator: Any,
    ) -> Iterator[dict[str, Any]]:
        original = getattr(orchestrator, "synthesis_handler")
        capture: dict[str, Any] = {
            "calls": 0,
            "args": [],
            "kwargs": {},
            "prompt": "",
        }

        def deterministic_synthesis(*args: Any, **kwargs: Any) -> str:
            capture["calls"] += 1
            capture["args"] = [self._json_safe(item) for item in args]
            capture["kwargs"] = {
                key: self._json_safe(value)
                for key, value in kwargs.items()
            }

            prompt = ""
            for item in args:
                if isinstance(item, str):
                    prompt = item
                    break

            if not prompt:
                for value in kwargs.values():
                    if isinstance(value, str):
                        prompt = value
                        break

            capture["prompt"] = prompt
            return (
                "CERTIFICATION SYNTHESIS: Grounding payload received. "
                "No external model was invoked."
            )

        setattr(orchestrator, "synthesis_handler", deterministic_synthesis)
        try:
            yield capture
        finally:
            setattr(orchestrator, "synthesis_handler", original)

    def _run_request(
        self,
        conversation_service: Any,
        orchestrator: Any,
        query: str,
        *,
        expected_gap: bool,
    ) -> dict[str, Any]:
        with self._capture_synthesis(orchestrator) as capture:
            response = conversation_service.ask(
                query,
                mode="full",
                metadata={
                    "certification": "genesis_ix_a4_3",
                    "expected_gap": expected_gap,
                },
            )

        data = mapping(response)
        metadata = mapping(data.get("metadata"))
        trace = data.get("trace") or []
        if trace and not isinstance(trace[0], Mapping):
            trace = [
                mapping(item)
                for item in trace
            ]

        grounding = (
            mapping(metadata.get("knowledge_grounding"))
            or mapping(metadata.get("grounding"))
            or mapping(metadata.get("executive_knowledge_state"))
        )

        prompt = str(capture.get("prompt") or "")

        return {
            "query": query,
            "response": data,
            "metadata": metadata,
            "trace": trace,
            "grounding": grounding,
            "synthesis_capture": capture,
            "prompt": prompt,
            "prompt_length": len(prompt),
            "prompt_sha256": self._sha256(prompt),
            "contains_grounding_marker": (
                "JARVIS KNOWLEDGE GROUNDING:" in prompt
            ),
            "contains_gap_marker": "Knowledge gaps:" in prompt,
            "contains_retrieved_marker": (
                "Retrieved catalog evidence:" in prompt
            ),
        }

    def _known_checks(
        self,
        trace: dict[str, Any],
    ) -> list[CertificationCheck]:
        response = trace.get("response") or {}
        metadata = trace.get("metadata") or {}
        prompt = trace.get("prompt") or ""
        grounding = trace.get("grounding") or {}

        evidence_count = (
            grounding.get("evidence_count")
            or metadata.get("evidence_count")
            or 0
        )
        grounding_status = (
            grounding.get("status")
            or metadata.get("grounding_status")
        )

        return [
            check(
                "KNOWN-RESPONSE",
                "Known request completes",
                str(response.get("state", "")).casefold() in {
                    "completed",
                    "conversationstate.completed",
                }
                or response.get("error") in (None, ""),
                "The canonical conversation service must complete the request.",
                actual=response.get("state"),
            ),
            check(
                "KNOWN-SYNTHESIS",
                "Synthesis handler receives request",
                (trace.get("synthesis_capture") or {}).get("calls") == 1,
                "The orchestrator must invoke synthesis exactly once.",
                expected=1,
                actual=(trace.get("synthesis_capture") or {}).get("calls"),
            ),
            check(
                "KNOWN-GROUNDING-MARKER",
                "Grounding reaches synthesis prompt",
                bool(trace.get("contains_grounding_marker")),
                "The prompt must contain the canonical grounding section.",
            ),
            check(
                "KNOWN-QUERY-PROMPT",
                "Operator query reaches synthesis prompt",
                str(trace.get("query")) in prompt,
                "The original question must remain in the grounded prompt.",
            ),
            check(
                "KNOWN-EVIDENCE",
                "Known request retrieves evidence",
                bool(evidence_count)
                or bool(trace.get("contains_retrieved_marker")),
                "A known catalog term must produce evidence.",
                expected="evidence_count > 0",
                actual=evidence_count,
            ),
            check(
                "KNOWN-STATUS",
                "Known request is grounded or partial",
                str(grounding_status).casefold() in {
                    "grounded",
                    "partial",
                }
                or bool(trace.get("contains_retrieved_marker")),
                "Known material must not be classified as a pure gap.",
                actual=grounding_status,
            ),
            check(
                "KNOWN-SOURCE",
                "Source provenance reaches prompt",
                any(
                    marker in prompt
                    for marker in (
                        "confidence=",
                        "assigned_by=",
                        "/media/",
                        "Source",
                    )
                ),
                "The grounded prompt must retain source provenance.",
            ),
        ]

    def _gap_checks(
        self,
        trace: dict[str, Any],
    ) -> list[CertificationCheck]:
        prompt = trace.get("prompt") or ""
        response = trace.get("response") or {}
        grounding = trace.get("grounding") or {}
        metadata = trace.get("metadata") or {}

        gap_count = (
            grounding.get("gap_count")
            or metadata.get("gap_count")
            or 0
        )
        grounding_status = (
            grounding.get("status")
            or metadata.get("grounding_status")
        )

        return [
            check(
                "GAP-SYNTHESIS",
                "Gap request reaches synthesis",
                (trace.get("synthesis_capture") or {}).get("calls") == 1,
                "Gap handling still uses the canonical synthesis path.",
                expected=1,
                actual=(trace.get("synthesis_capture") or {}).get("calls"),
            ),
            check(
                "GAP-GROUNDING-MARKER",
                "Gap prompt contains grounding section",
                bool(trace.get("contains_grounding_marker")),
                "The grounding section must be present even without evidence.",
            ),
            check(
                "GAP-DECLARATION",
                "Knowledge gap is explicit",
                bool(gap_count)
                or bool(trace.get("contains_gap_marker"))
                or str(grounding_status).casefold() == "gap",
                "Unknown material must generate an explicit KnowledgeGap.",
                expected="gap",
                actual={
                    "gap_count": gap_count,
                    "status": grounding_status,
                },
            ),
            check(
                "GAP-NO-EXTERNAL-LLM",
                "Certification avoids external model invocation",
                str(response.get("answer", "")).startswith(
                    "CERTIFICATION SYNTHESIS:"
                ),
                "The temporary deterministic handler must replace external synthesis.",
                actual=response.get("answer"),
            ),
            check(
                "GAP-RECOMMENDATION",
                "Gap prompt preserves acquisition guidance",
                any(
                    marker in prompt
                    for marker in (
                        "Queue targeted acquisition",
                        "Knowledge gaps:",
                        "No catalog evidence was retrieved.",
                    )
                ),
                "The gap must retain a recommended follow-on action.",
            ),
        ]

    def _source_contract_checks(self) -> list[CertificationCheck]:
        orchestrator_path = (
            self.repository_root / "core/conversation/orchestrator.py"
        )
        grounding_path = (
            self.repository_root / "core/conversation/grounding.py"
        )
        catalog_path = (
            self.repository_root / "core/knowledge_catalog/search.py"
        )
        runtime_search_path = (
            self.repository_root
            / "core/knowledge_catalog/materialization/search.py"
        )

        sources = {
            "orchestrator": orchestrator_path.read_text(
                encoding="utf-8",
                errors="replace",
            ),
            "grounding": grounding_path.read_text(
                encoding="utf-8",
                errors="replace",
            ),
            "catalog": catalog_path.read_text(
                encoding="utf-8",
                errors="replace",
            ),
            "runtime": runtime_search_path.read_text(
                encoding="utf-8",
                errors="replace",
            ),
        }

        return [
            check(
                "SOURCE-GROUND",
                "Orchestrator invokes grounding",
                "self.grounding_service.ground(context)"
                in sources["orchestrator"],
                "Grounding must precede synthesis.",
            ),
            check(
                "SOURCE-AWARENESS",
                "Awareness consumes grounding",
                "self.awareness_service.assess(grounding)"
                in sources["orchestrator"],
                "Knowledge awareness must consume GroundingResult.",
            ),
            check(
                "SOURCE-SYNTHESIS",
                "Grounding augments synthesis input",
                "grounding.synthesis_input(synthesis_input)"
                in sources["orchestrator"],
                "Retrieved evidence must reach synthesis.",
            ),
            check(
                "SOURCE-DELEGATION",
                "Catalog search delegates to runtime search",
                "search_runtime_knowledge(" in sources["catalog"],
                "The canonical search API must use materialized retrieval.",
            ),
            check(
                "SOURCE-FTS",
                "Runtime retrieval uses FTS",
                "runtime_chunks_fts" in sources["runtime"]
                and "MATCH" in sources["runtime"],
                "Mark I retrieval must exercise SQLite FTS.",
            ),
            check(
                "SOURCE-GAP",
                "Grounding declares gaps",
                "KnowledgeGap(" in sources["grounding"],
                "No-result retrieval must create KnowledgeGap.",
            ),
        ]

    @staticmethod
    def _identity(value: Any) -> dict[str, Any] | None:
        if value is None:
            return None
        return {
            "module": type(value).__module__,
            "type": type(value).__name__,
            "qualified_type": (
                f"{type(value).__module__}.{type(value).__name__}"
            ),
        }

    @staticmethod
    def _callable_identity(value: Any) -> dict[str, Any] | None:
        if value is None:
            return None
        return {
            "module": getattr(value, "__module__", type(value).__module__),
            "name": getattr(value, "__name__", type(value).__name__),
            "qualname": getattr(
                value,
                "__qualname__",
                type(value).__qualname__,
            ),
            "signature": (
                str(inspect.signature(value))
                if callable(value)
                else None
            ),
        }

    @staticmethod
    def _sha256(value: str) -> str:
        import hashlib
        return hashlib.sha256(value.encode("utf-8")).hexdigest()

    @staticmethod
    def _json_safe(value: Any) -> Any:
        if value is None or isinstance(value, (str, int, float, bool)):
            return value
        if isinstance(value, Mapping):
            return {
                str(key): EndToEndRetrievalTracer._json_safe(item)
                for key, item in value.items()
            }
        if isinstance(value, (list, tuple)):
            return [
                EndToEndRetrievalTracer._json_safe(item)
                for item in value
            ]
        return mapping(value) or repr(value)
