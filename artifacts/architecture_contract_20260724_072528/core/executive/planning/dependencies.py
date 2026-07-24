"""Dependency graph construction and validation."""

from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass

from core.executive.planning.errors import (
    DependencyCycleError,
    DependencyGraphError,
    MissingPlanElementError,
)
from core.executive.planning.models import Dependency, Mission


def collect_plan_element_ids(mission: Mission) -> tuple[str, ...]:
    """Collect every canonical element identifier in hierarchy order."""

    identifiers: list[str] = [mission.mission_id]

    for objective in mission.objectives:
        identifiers.append(objective.objective_id)

        for task in objective.tasks:
            identifiers.append(task.task_id)

            for activity in task.activities:
                identifiers.append(activity.activity_id)

                for command in activity.commands:
                    identifiers.append(command.command_id)

    return tuple(identifiers)


@dataclass(frozen=True, slots=True)
class DependencyGraph:
    """Validated directed acyclic dependency graph."""

    element_ids: tuple[str, ...]
    dependencies: tuple[Dependency, ...]

    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        """Validate references, duplicate edges, and cycle freedom."""

        elements = set(self.element_ids)

        if len(elements) != len(self.element_ids):
            raise DependencyGraphError(
                "Dependency graph contains duplicate element identifiers"
            )

        seen_edges: set[tuple[str, str, str]] = set()

        for dependency in self.dependencies:
            if dependency.predecessor_id not in elements:
                raise MissingPlanElementError(
                    "Dependency references missing predecessor "
                    f"{dependency.predecessor_id}"
                )

            if dependency.successor_id not in elements:
                raise MissingPlanElementError(
                    "Dependency references missing successor "
                    f"{dependency.successor_id}"
                )

            edge = (
                dependency.predecessor_id,
                dependency.successor_id,
                dependency.dependency_type.value,
            )

            if edge in seen_edges:
                raise DependencyGraphError(
                    "Duplicate dependency edge detected: "
                    f"{dependency.predecessor_id} -> "
                    f"{dependency.successor_id}"
                )

            seen_edges.add(edge)

        cycle = self.find_cycle()

        if cycle:
            raise DependencyCycleError(cycle)

    def adjacency(self) -> dict[str, tuple[str, ...]]:
        """Return deterministic predecessor-to-successor adjacency."""

        mutable: dict[str, list[str]] = defaultdict(list)

        for dependency in self.dependencies:
            mutable[dependency.predecessor_id].append(
                dependency.successor_id
            )

        return {
            element_id: tuple(sorted(mutable.get(element_id, [])))
            for element_id in sorted(self.element_ids)
        }

    def predecessors(self, element_id: str) -> tuple[str, ...]:
        """Return direct predecessors of one plan element."""

        return tuple(
            sorted(
                dependency.predecessor_id
                for dependency in self.dependencies
                if dependency.successor_id == element_id
            )
        )

    def successors(self, element_id: str) -> tuple[str, ...]:
        """Return direct successors of one plan element."""

        return tuple(
            sorted(
                dependency.successor_id
                for dependency in self.dependencies
                if dependency.predecessor_id == element_id
            )
        )

    def find_cycle(self) -> tuple[str, ...] | None:
        """Return one dependency cycle, or None when acyclic."""

        adjacency = self.adjacency()
        visiting: set[str] = set()
        visited: set[str] = set()
        stack: list[str] = []

        def visit(node: str) -> tuple[str, ...] | None:
            visiting.add(node)
            stack.append(node)

            for successor in adjacency.get(node, ()):
                if successor in visiting:
                    cycle_start = stack.index(successor)
                    return tuple(stack[cycle_start:] + [successor])

                if successor not in visited:
                    cycle = visit(successor)

                    if cycle:
                        return cycle

            stack.pop()
            visiting.remove(node)
            visited.add(node)
            return None

        for element_id in sorted(self.element_ids):
            if element_id not in visited:
                cycle = visit(element_id)

                if cycle:
                    return cycle

        return None

    def topological_order(self) -> tuple[str, ...]:
        """Return deterministic dependency-safe ordering."""

        adjacency = self.adjacency()
        indegree = {element_id: 0 for element_id in self.element_ids}

        for successors in adjacency.values():
            for successor in successors:
                indegree[successor] += 1

        available = deque(
            sorted(
                element_id
                for element_id, degree in indegree.items()
                if degree == 0
            )
        )

        ordered: list[str] = []

        while available:
            node = available.popleft()
            ordered.append(node)

            for successor in adjacency.get(node, ()):
                indegree[successor] -= 1

                if indegree[successor] == 0:
                    available.append(successor)
                    available = deque(sorted(available))

        if len(ordered) != len(self.element_ids):
            cycle = self.find_cycle()

            if cycle:
                raise DependencyCycleError(cycle)

            raise DependencyGraphError(
                "Dependency graph could not be topologically sorted"
            )

        return tuple(ordered)


def build_dependency_graph(
    mission: Mission,
    dependencies: tuple[Dependency, ...],
) -> DependencyGraph:
    """Build and validate a dependency graph for one mission."""

    return DependencyGraph(
        element_ids=collect_plan_element_ids(mission),
        dependencies=dependencies,
    )
