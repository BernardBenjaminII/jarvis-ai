from __future__ import annotations

from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Iterable

from .directorate_contracts import DirectorateEdgeKind, DirectorateNodeKind
from .directorate_models import DirectorateEdge, DirectorateNode
from ..fingerprints import canonical_fingerprint


@dataclass(frozen=True)
class DirectorateAssignmentRule:
    directorate_key: str
    path_prefixes: tuple[str, ...]
    priority: int

    def matches(self, path: str) -> bool:
        normalized = path.replace("\\", "/").strip("/")
        return any(
            normalized == prefix or normalized.startswith(prefix + "/")
            for prefix in self.path_prefixes
        )


ASSIGNMENT_RULES: tuple[DirectorateAssignmentRule, ...] = (
    DirectorateAssignmentRule("governance", ("core/governance", "docs/constitution", "docs/governance"), 100),
    DirectorateAssignmentRule("knowledge", ("core/knowledge", "knowledge", "docs/knowledge"), 95),
    DirectorateAssignmentRule("reasoning", ("core/reasoning", "docs/reasoning"), 95),
    DirectorateAssignmentRule("planning", ("core/planning", "docs/planning"), 90),
    DirectorateAssignmentRule("operations", ("core/operations", "operations", "docs/operations"), 90),
    DirectorateAssignmentRule("intelligence_acquisition", ("core/acquisition", "acquisition", "docs/acquisition"), 90),
    DirectorateAssignmentRule("software_engineering", ("core", "tests", "dev", "scripts", "config"), 50),
    DirectorateAssignmentRule("executive", ("docs/executive", "executive"), 40),
)


def choose_directorate(path: str) -> str:
    normalized = path.replace("\\", "/").strip("/")
    matches = [rule for rule in ASSIGNMENT_RULES if rule.matches(normalized)]
    if not matches:
        return "software_engineering"
    return sorted(matches, key=lambda rule: (-rule.priority, rule.directorate_key))[0].directorate_key


def build_assignment_edges(
    nodes: Iterable[DirectorateNode],
) -> tuple[DirectorateEdge, ...]:
    node_by_id = {node.node_id: node for node in nodes}
    edges: list[DirectorateEdge] = []

    for node in sorted(node_by_id.values(), key=lambda item: item.node_id):
        if node.node_kind is not DirectorateNodeKind.OWNERSHIP_DOMAIN:
            continue

        path = str(node.attributes.get("repository_path", "")).strip()
        directorate_key = choose_directorate(path)
        directorate_id = f"directorate:{directorate_key}"
        if directorate_id not in node_by_id:
            continue

        for edge_kind in (
            DirectorateEdgeKind.OWNS,
            DirectorateEdgeKind.MAINTAINS,
        ):
            edge_id = f"{edge_kind.value}:{directorate_id}:{node.node_id}"
            attributes = {
                "repository_path": path,
                "assignment_rule": directorate_key,
                "deterministic": True,
            }
            basis = {
                "edge_id": edge_id,
                "source_node_id": directorate_id,
                "target_node_id": node.node_id,
                "edge_kind": edge_kind.value,
                "attributes": attributes,
            }
            edges.append(
                DirectorateEdge(
                    edge_id=edge_id,
                    source_node_id=directorate_id,
                    target_node_id=node.node_id,
                    edge_kind=edge_kind,
                    attributes=attributes,
                    fingerprint=canonical_fingerprint(basis),
                )
            )

    return tuple(sorted(edges, key=lambda item: item.edge_id))
