"""Canonical knowledge grounding for JARVIS Convergence C-4."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping

from core.conversation.contracts import CompiledObjective, ExecutiveRequestContext
from core.knowledge_catalog.config import DEFAULT_CATALOG_DB


CatalogSearch = Callable[[str, int], Iterable[Mapping[str, Any]]]


@dataclass(frozen=True, slots=True)
class GroundingEvidence:
    evidence_id: str
    objective_id: str
    query: str
    subject: str
    source_path: str
    confidence: float
    assigned_by: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "evidence_id": self.evidence_id,
            "objective_id": self.objective_id,
            "query": self.query,
            "subject": self.subject,
            "source_path": self.source_path,
            "confidence": self.confidence,
            "assigned_by": self.assigned_by,
        }


@dataclass(frozen=True, slots=True)
class KnowledgeGap:
    objective_id: str
    query: str
    reason: str
    recommended_action: str = "Queue targeted acquisition and assimilation."

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
            "evidence": [item.to_dict() for item in self.evidence],
            "gap": None if self.gap is None else self.gap.to_dict(),
        }


@dataclass(frozen=True, slots=True)
class GroundingResult:
    objectives: tuple[ObjectiveGrounding, ...]
    catalog_path: str

    @property
    def evidence(self) -> tuple[GroundingEvidence, ...]:
        return tuple(item for objective in self.objectives for item in objective.evidence)

    @property
    def gaps(self) -> tuple[KnowledgeGap, ...]:
        return tuple(objective.gap for objective in self.objectives if objective.gap is not None)

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
            "gap_count": len(self.gaps),
            "objectives": [item.to_dict() for item in self.objectives],
            "gaps": [item.to_dict() for item in self.gaps],
        }

    def for_objective(self, objective_id: str) -> ObjectiveGrounding | None:
        return next((item for item in self.objectives if item.objective_id == objective_id), None)

    def synthesis_input(self, operator_input: str) -> str:
        lines = [operator_input.strip(), "", "JARVIS KNOWLEDGE GROUNDING:"]
        if self.evidence:
            lines.append("Retrieved catalog evidence:")
            for item in self.evidence:
                lines.append(
                    f"- [{item.subject}] {item.source_path} "
                    f"(confidence={item.confidence:.3f}, assigned_by={item.assigned_by})"
                )
        else:
            lines.append("- No catalog evidence was retrieved.")
        if self.gaps:
            lines.append("Knowledge gaps:")
            for gap in self.gaps:
                lines.append(f"- {gap.query}: {gap.reason}")
        lines.append(
            "Use retrieved evidence when relevant. State uncertainty and do not invent "
            "catalog facts when a gap is present."
        )
        return "\n".join(lines)


class CatalogGroundingService:
    """Retrieve deterministic catalog evidence and declare explicit gaps."""

    def __init__(
        self,
        *,
        database_path: str | Path = DEFAULT_CATALOG_DB,
        search_handler: CatalogSearch | None = None,
        limit_per_objective: int = 8,
    ) -> None:
        self.database_path = Path(database_path)
        self.limit_per_objective = max(1, int(limit_per_objective))
        self.search_handler = search_handler or self._search_catalog

    def _search_catalog(self, query: str, limit: int) -> Iterable[Mapping[str, Any]]:
        from core.knowledge_catalog.search import search_catalog
        return search_catalog(query, db_path=self.database_path, limit=limit)

    def ground(self, context: ExecutiveRequestContext) -> GroundingResult:
        grounded: list[ObjectiveGrounding] = []
        for objective in context.objectives:
            grounded.append(self._ground_objective(objective))
        return GroundingResult(
            objectives=tuple(grounded),
            catalog_path=str(self.database_path),
        )

    def search_for_director(self, objective: str, context: dict[str, Any]) -> dict[str, Any]:
        objective_id = str(context.get("objective_id") or "director-query")
        compiled = CompiledObjective(
            objective_id=objective_id,
            text=objective,
            ordinal=1,
            routing_hints=("knowledge",),
        )
        result = self._ground_objective(compiled)
        return {
            "mode": "catalog_grounding",
            "status": result.status,
            "query": objective,
            "evidence": [item.to_dict() for item in result.evidence],
            "gap": None if result.gap is None else result.gap.to_dict(),
        }

    def _ground_objective(self, objective: CompiledObjective) -> ObjectiveGrounding:
        try:
            rows = list(self.search_handler(objective.text, self.limit_per_objective))
        except Exception as exc:
            return ObjectiveGrounding(
                objective_id=objective.objective_id,
                query=objective.text,
                evidence=(),
                gap=KnowledgeGap(
                    objective_id=objective.objective_id,
                    query=objective.text,
                    reason=f"Knowledge catalog unavailable: {exc}",
                    recommended_action="Restore catalog availability, then retry retrieval.",
                ),
            )

        evidence: list[GroundingEvidence] = []
        seen: set[tuple[str, str]] = set()
        for ordinal, row in enumerate(rows, start=1):
            data = dict(row)
            subject = str(data.get("subject") or "unclassified")
            source_path = str(data.get("file_path") or data.get("source_path") or "")
            key = (subject, source_path)
            if key in seen:
                continue
            seen.add(key)
            try:
                confidence = float(data.get("confidence", 0.0) or 0.0)
            except (TypeError, ValueError):
                confidence = 0.0
            evidence.append(
                GroundingEvidence(
                    evidence_id=f"{objective.objective_id}:catalog:{ordinal}",
                    objective_id=objective.objective_id,
                    query=objective.text,
                    subject=subject,
                    source_path=source_path,
                    confidence=max(0.0, min(1.0, confidence)),
                    assigned_by=str(data.get("assigned_by") or "catalog"),
                )
            )

        gap = None
        if not evidence:
            gap = KnowledgeGap(
                objective_id=objective.objective_id,
                query=objective.text,
                reason="No matching catalog evidence was found.",
            )
        return ObjectiveGrounding(
            objective_id=objective.objective_id,
            query=objective.text,
            evidence=tuple(evidence),
            gap=gap,
        )
