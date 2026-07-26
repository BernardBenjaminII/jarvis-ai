from __future__ import annotations

from collections import defaultdict
from typing import Iterable

from .contracts import ExecutionGraph, ExecutionNode
from .errors import MissionDependencyCycleError


def build_execution_graph(nodes: Iterable[ExecutionNode]) -> ExecutionGraph:
    ordered_nodes = tuple(sorted(nodes, key=lambda node: node.node_id))
    node_ids = {node.node_id for node in ordered_nodes}

    incoming: dict[str, int] = {node_id: 0 for node_id in node_ids}
    outgoing: dict[str, list[str]] = defaultdict(list)

    for node in ordered_nodes:
        for dependency_id in node.dependency_ids:
            if dependency_id not in node_ids:
                raise ValueError(
                    f"Unknown dependency {dependency_id!r} for node {node.node_id!r}."
                )
            outgoing[dependency_id].append(node.node_id)
            incoming[node.node_id] += 1

    ready = sorted(node_id for node_id, count in incoming.items() if count == 0)
    result: list[str] = []

    while ready:
        node_id = ready.pop(0)
        result.append(node_id)
        for dependent in sorted(outgoing[node_id]):
            incoming[dependent] -= 1
            if incoming[dependent] == 0:
                ready.append(dependent)
                ready.sort()

    if len(result) != len(node_ids):
        unresolved = sorted(node_id for node_id, count in incoming.items() if count)
        raise MissionDependencyCycleError(
            "Execution graph contains a dependency cycle involving: "
            + ", ".join(unresolved)
        )

    return ExecutionGraph(
        nodes=ordered_nodes,
        topological_order=tuple(result),
    )
