from __future__ import annotations
from pathlib import PurePosixPath
from typing import Any
from ..fingerprints import canonical_fingerprint
from .repository_classifier import classify_repository_path, infer_lifecycle_state, normalize_path
from .repository_contracts import RepositoryEdgeKind, RepositoryNodeKind
from .repository_models import RepositoryEdge, RepositoryNode

def _node(node_id: str, kind: RepositoryNodeKind, label: str, path: str, attrs: dict[str, Any]) -> RepositoryNode:
    basis = {"node_id": node_id, "node_kind": kind.value, "label": label, "path": path, "attributes": attrs}
    return RepositoryNode(node_id, kind, label, path, attrs, canonical_fingerprint(basis))

def _edge(edge_id: str, source: str, target: str, kind: RepositoryEdgeKind, attrs: dict[str, Any]) -> RepositoryEdge:
    basis = {"edge_id": edge_id, "source_node_id": source, "target_node_id": target,
             "edge_kind": kind.value, "attributes": attrs}
    return RepositoryEdge(edge_id, source, target, kind, attrs, canonical_fingerprint(basis))

def _extract_path(node: dict[str, Any]) -> str:
    attrs = dict(node.get("attributes", {}))
    for candidate in (attrs.get("path"), attrs.get("repository_path"),
                      attrs.get("artifact_path"), node.get("path"), node.get("label")):
        value = str(candidate or "").strip()
        if value:
            return normalize_path(value)
    return normalize_path(str(node.get("node_id", "unknown")))

def _parent_paths(path: str) -> tuple[str, ...]:
    result, current = [], PurePosixPath(path).parent
    while str(current) not in {".", "/", ""}:
        result.append(str(current))
        current = current.parent
    return tuple(reversed(result))

def build_repository_projection(authority_nodes: list[dict[str, Any]]) -> tuple[tuple[RepositoryNode, ...], tuple[RepositoryEdge, ...]]:
    nodes, edges = {}, {}
    root_id = "repository:root"
    nodes[root_id] = _node(root_id, RepositoryNodeKind.REPOSITORY, "JARVIS Repository", ".", {"lifecycle_state": "implemented"})
    for source in sorted(authority_nodes, key=lambda x: str(x.get("node_id", ""))):
        if str(source.get("node_kind", "")) != "governed_artifact":
            continue
        source_id = str(source.get("node_id", ""))
        path = _extract_path(source)
        attrs = dict(source.get("attributes", {}))
        kind = classify_repository_path(path)
        lifecycle = infer_lifecycle_state(kind, attrs)
        artifact_id = f"repository_artifact:{source_id}"
        nodes[artifact_id] = _node(
            artifact_id, kind, PurePosixPath(path).name or path, path,
            {**attrs, "source_authority_node_id": source_id, "lifecycle_state": lifecycle.value}
        )
        parent_id = root_id
        for parent_path in _parent_paths(path):
            package_id = f"repository_path:{parent_path}"
            if package_id not in nodes:
                nodes[package_id] = _node(
                    package_id, RepositoryNodeKind.PACKAGE,
                    PurePosixPath(parent_path).name, parent_path,
                    {"synthetic": True, "lifecycle_state": "implemented"}
                )
                eid = f"contains:{parent_id}:{package_id}"
                edges[eid] = _edge(eid, parent_id, package_id, RepositoryEdgeKind.CONTAINS, {"synthetic": True})
            parent_id = package_id
        eid = f"contains:{parent_id}:{artifact_id}"
        edges[eid] = _edge(eid, parent_id, artifact_id, RepositoryEdgeKind.CONTAINS, {"source_authority_node_id": source_id})
        bid = f"belongs:{artifact_id}:{parent_id}"
        edges[bid] = _edge(bid, artifact_id, parent_id, RepositoryEdgeKind.BELONGS_TO, {})
    return tuple(sorted(nodes.values(), key=lambda x: x.node_id)), tuple(sorted(edges.values(), key=lambda x: x.edge_id))
