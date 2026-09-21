"""Canonical knowledge grounding for JARVIS Convergence C-4."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping

from core.conversation.contracts import (
    CompiledObjective,
    ExecutiveRequestContext,
)
from core.knowledge_catalog.config import DEFAULT_CATALOG_DB


CatalogSearch = Callable[
    [str, int],
    Iterable[Mapping[str, Any]],
]


def _unit(value: Any) -> float:
    try:
        score = float(value)
    except (TypeError, ValueError):
        return 0.0

    if score != score:
        return 0.0

    if score in (float("inf"), float("-inf")):
        return 0.0

    return max(0.0, min(1.0, score))


def _optional_int(value: Any) -> int | None:
    try:
        if value is None:
            return None
        return int(value)
    except (TypeError, ValueError):
        return None


@dataclass(frozen=True, slots=True)
class GroundingEvidence:
    evidence_id: str
    objective_id: str
    query: str
    subject: str
    source_path: str
    excerpt: str
    confidence: float
    assigned_by: str

    # Durable runtime identity.
    chunk_id: int | None = None
    document_id: int | None = None

    # Retrieval / qualification diagnostics.
    qualification_score: float = 0.0
    semantic_score: float = 0.0
    hybrid_score: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "evidence_id": self.evidence_id,
            "objective_id": self.objective_id,
            "query": self.query,
            "subject": self.subject,
            "source_path": self.source_path,
            "excerpt": self.excerpt,
            "confidence": self.confidence,
            "assigned_by": self.assigned_by,
            "chunk_id": self.chunk_id,
            "document_id": self.document_id,
            "qualification_score": self.qualification_score,
            "semantic_score": self.semantic_score,
            "hybrid_score": self.hybrid_score,
        }


@dataclass(frozen=True, slots=True)
class KnowledgeGap:
    objective_id: str
    query: str
    reason: str
    recommended_action: str = (
        "Queue targeted acquisition and assimilation."
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "objective_id": self.objective_id,
            "query": self.query,
            "reason": self.reason,
            "recommended_action": self.recommended_action,
        }


@dataclass(frozen=True, slots=True)
class ObjectiveGrounding:
    objective_id: str
    query: str
    evidence: tuple[GroundingEvidence, ...]
    gap: KnowledgeGap | None

    @property
    def status(self) -> str:
        return "grounded" if self.evidence else "gap"

    def to_dict(self) -> dict[str, Any]:
        return {
            "objective_id": self.objective_id,
            "query": self.query,
            "status": self.status,
            "evidence": [
                item.to_dict()
                for item in self.evidence
            ],
            "gap": (
                None
                if self.gap is None
                else self.gap.to_dict()
            ),
        }


# GENESIS_RECALL_R4_R11_A5_R9_R17_R4_R2
@dataclass(frozen=True, slots=True)
class GroundingResult:
    objectives: tuple[ObjectiveGrounding, ...]
    catalog_path: str

    @property
    def evidence(self) -> tuple[GroundingEvidence, ...]:
        return tuple(
            item
            for objective in self.objectives
            for item in objective.evidence
        )

    @property
    def gaps(self) -> tuple[KnowledgeGap, ...]:
        return tuple(
            objective.gap
            for objective in self.objectives
            if objective.gap is not None
        )

    @property
    def status(self) -> str:
        if self.evidence and not self.gaps:
            return "grounded"

        if self.evidence:
            return "partial"

        return "gap"

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "catalog_path": self.catalog_path,
            "evidence_count": len(self.evidence),
            "evidence": [
                item.to_dict()
                for item in self.evidence
            ],
            "gap_count": len(self.gaps),
            "objectives": [
                item.to_dict()
                for item in self.objectives
            ],
            "gaps": [
                item.to_dict()
                for item in self.gaps
            ],
        }

    def for_objective(
        self,
        objective_id: str,
    ) -> ObjectiveGrounding | None:
        return next(
            (
                item
                for item in self.objectives
                if item.objective_id == objective_id
            ),
            None,
        )

    def synthesis_input(
        self,
        operator_input: str,
    ) -> str:

        lines = [
            operator_input.strip(),
            "",
            "JARVIS KNOWLEDGE GROUNDING:",
        ]

        if self.evidence:
            lines.append(
                "Retrieved catalog evidence:"
            )

            for item in self.evidence:
                identity = ""

                if item.chunk_id is not None:
                    identity = (
                        f", chunk={item.chunk_id}"
                    )

                lines.append(
                    f"- [{item.subject}] "
                    f"{item.source_path} "
                    f"(confidence={item.confidence:.3f}"
                    f"{identity}, "
                    f"assigned_by={item.assigned_by})"
                )

                if item.excerpt:
                    lines.append(
                        f"  EXCERPT: {item.excerpt}"
                    )

        else:
            lines.append(
                "- No catalog evidence was retrieved."
            )

        if self.gaps:
            lines.append("Knowledge gaps:")

            for gap in self.gaps:
                lines.append(
                    f"- {gap.query}: {gap.reason}"
                )

        lines.append(
            "Use retrieved evidence when relevant. "
            "State uncertainty and do not invent catalog "
            "facts when a gap is present."
        )

        return "\n".join(lines)


class CatalogGroundingService:
    """
    Retrieve deterministic qualified catalog evidence and declare
    explicit gaps.

    Qualified rows are deduplicated by runtime evidence identity,
    not merely by document path. Multiple distinct chunks from the
    same source may therefore survive grounding.

    Per-document diversity limits prevent a single source from
    monopolizing the Executive grounding context.
    """

    def __init__(
        self,
        *,
        database_path: str | Path = DEFAULT_CATALOG_DB,
        search_handler: CatalogSearch | None = None,
        limit_per_objective: int = 8,
        max_per_document: int = 3,
    ) -> None:

        self.database_path = Path(database_path)

        self.limit_per_objective = max(
            1,
            int(limit_per_objective),
        )

        self.max_per_document = max(
            1,
            int(max_per_document),
        )

        self.search_handler = (
            search_handler
            or self._search_catalog
        )

    def _search_catalog(
        self,
        query: str,
        limit: int,
    ) -> Iterable[Mapping[str, Any]]:

        from core.knowledge_catalog.qualified_search import (
            search_qualified_catalog,
        )

        return search_qualified_catalog(
            query,
            db_path=self.database_path,
            limit=limit,
        )

    def ground(
        self,
        context: ExecutiveRequestContext,
    ) -> GroundingResult:

        grounded: list[ObjectiveGrounding] = []

        for objective in context.objectives:
            grounded.append(
                self._ground_objective(objective)
            )

        return GroundingResult(
            objectives=tuple(grounded),
            catalog_path=str(self.database_path),
        )

    def search_for_director(
        self,
        objective: str,
        context: dict[str, Any],
    ) -> dict[str, Any]:

        objective_id = str(
            context.get("objective_id")
            or "director-query"
        )

        compiled = CompiledObjective(
            objective_id=objective_id,
            text=objective,
            ordinal=1,
            routing_hints=("knowledge",),
        )

        result = self._ground_objective(
            compiled
        )

        return {
            "mode": "catalog_grounding",
            "status": result.status,
            "query": objective,
            "evidence": [
                item.to_dict()
                for item in result.evidence
            ],
            "gap": (
                None
                if result.gap is None
                else result.gap.to_dict()
            ),
        }

    @staticmethod
    def _row_rank(
        data: Mapping[str, Any],
    ) -> tuple[float, float, float, float]:

        return (
            _unit(
                data.get(
                    "qualification_score",
                    0.0,
                )
            ),
            _unit(
                data.get(
                    "hybrid_score",
                    0.0,
                )
            ),
            _unit(
                data.get(
                    "semantic_score",
                    0.0,
                )
            ),
            _unit(
                data.get(
                    "confidence",
                    0.0,
                )
            ),
        )

    @staticmethod
    def _identity_key(
        data: Mapping[str, Any],
        subject: str,
        source_path: str,
        ordinal: int,
    ) -> tuple[Any, ...]:

        chunk_id = _optional_int(
            data.get("chunk_id")
        )

        if chunk_id is not None:
            return (
                "chunk",
                chunk_id,
            )

        source_id = data.get("source_id")

        if source_id not in (
            None,
            "",
        ):
            return (
                "source",
                str(source_id),
            )

        excerpt = str(
            data.get("excerpt")
            or data.get("chunk_text")
            or ""
        )

        if excerpt:
            return (
                "excerpt",
                subject,
                source_path,
                excerpt,
            )

        return (
            "ordinal",
            subject,
            source_path,
            ordinal,
        )

    @staticmethod
    def _document_key(
        data: Mapping[str, Any],
        subject: str,
        source_path: str,
    ) -> tuple[Any, ...]:

        document_id = _optional_int(
            data.get("document_id")
        )

        if document_id is not None:
            return (
                "document",
                document_id,
            )

        return (
            "source",
            subject,
            source_path,
        )

    def _ground_objective(
        self,
        objective: CompiledObjective,
    ) -> ObjectiveGrounding:

        try:
            raw_rows = list(
                self.search_handler(
                    objective.text,
                    self.limit_per_objective,
                )
            )

        except Exception as exc:
            return ObjectiveGrounding(
                objective_id=objective.objective_id,
                query=objective.text,
                evidence=(),
                gap=KnowledgeGap(
                    objective_id=objective.objective_id,
                    query=objective.text,
                    reason=(
                        "Knowledge catalog unavailable: "
                        f"{exc}"
                    ),
                    recommended_action=(
                        "Restore catalog availability, "
                        "then retry retrieval."
                    ),
                ),
            )

        # ----------------------------------------------------------
        # Normalize and rank the already-qualified rows.
        #
        # The previous implementation deduplicated by
        # (subject, source_path). That collapsed every qualified
        # chunk from a document into one arbitrary representative.
        #
        # Here we preserve runtime chunk identity and use the
        # qualification/retrieval signals already computed below.
        # ----------------------------------------------------------

        normalized: list[
            tuple[
                tuple[float, float, float, float],
                int,
                dict[str, Any],
            ]
        ] = []

        for ordinal, row in enumerate(
            raw_rows,
            start=1,
        ):
            data = dict(row)

            normalized.append(
                (
                    self._row_rank(data),
                    ordinal,
                    data,
                )
            )

        # Highest qualification/retrieval quality first.
        # Original ordinal provides deterministic tie-breaking.
        normalized.sort(
            key=lambda item: (
                -item[0][0],
                -item[0][1],
                -item[0][2],
                -item[0][3],
                item[1],
            )
        )

        evidence: list[GroundingEvidence] = []

        seen_evidence: set[
            tuple[Any, ...]
        ] = set()

        per_document: dict[
            tuple[Any, ...],
            int,
        ] = {}

        for _, ordinal, data in normalized:

            subject = str(
                data.get("subject")
                or "unclassified"
            )

            source_path = str(
                data.get("file_path")
                or data.get("source_path")
                or ""
            )

            evidence_key = self._identity_key(
                data,
                subject,
                source_path,
                ordinal,
            )

            if evidence_key in seen_evidence:
                continue

            document_key = self._document_key(
                data,
                subject,
                source_path,
            )

            document_count = per_document.get(
                document_key,
                0,
            )

            if (
                document_count
                >= self.max_per_document
            ):
                continue

            seen_evidence.add(
                evidence_key
            )

            per_document[document_key] = (
                document_count + 1
            )

            evidence.append(
                GroundingEvidence(
                    evidence_id=(
                        f"{objective.objective_id}"
                        f":catalog:{ordinal}"
                    ),
                    objective_id=(
                        objective.objective_id
                    ),
                    query=objective.text,
                    subject=subject,
                    source_path=source_path,
                    excerpt=str(
                        data.get("excerpt")
                        or data.get("chunk_text")
                        or ""
                    ),
                    confidence=_unit(
                        data.get(
                            "confidence",
                            0.0,
                        )
                    ),
                    assigned_by=str(
                        data.get("assigned_by")
                        or "catalog"
                    ),
                    chunk_id=_optional_int(
                        data.get("chunk_id")
                    ),
                    document_id=_optional_int(
                        data.get("document_id")
                    ),
                    qualification_score=_unit(
                        data.get(
                            "qualification_score",
                            0.0,
                        )
                    ),
                    semantic_score=_unit(
                        data.get(
                            "semantic_score",
                            0.0,
                        )
                    ),
                    hybrid_score=_unit(
                        data.get(
                            "hybrid_score",
                            0.0,
                        )
                    ),
                )
            )

            if (
                len(evidence)
                >= self.limit_per_objective
            ):
                break

        gap = None

        if not evidence:
            gap = KnowledgeGap(
                objective_id=objective.objective_id,
                query=objective.text,
                reason=(
                    "No matching catalog evidence "
                    "was found."
                ),
            )

        return ObjectiveGrounding(
            objective_id=objective.objective_id,
            query=objective.text,
            evidence=tuple(evidence),
            gap=gap,
        )
