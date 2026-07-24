"""Capability-aware director registry used by the Mission Engine."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import replace

from core.executive.capabilities import (
    DirectorDescriptor,
    DirectorReadiness,
    RoutingCandidate,
    RoutingDecision,
    normalize_capability,
    normalize_director_name,
)
from core.executive.contracts import DirectorHandler, DirectorNotRegisteredError


class DirectorRegistry:
    def __init__(self) -> None:
        self._handlers: dict[str, DirectorHandler] = {}
        self._descriptors: dict[str, DirectorDescriptor] = {}

    def register(
        self,
        name: str,
        handler: DirectorHandler,
        *,
        capabilities: Iterable[str] = (),
        description: str = "",
        priority: int = 100,
        readiness: DirectorReadiness = DirectorReadiness.READY,
        metadata: dict | None = None,
        replace_existing: bool = False,
        replace: bool | None = None,
    ) -> None:
        if replace is not None:
            replace_existing = replace

        normalized = normalize_director_name(name)
        if normalized in self._handlers and not replace_existing:
            raise ValueError(f"Director already registered: {normalized}")

        self._handlers[normalized] = handler
        self._descriptors[normalized] = DirectorDescriptor(
            name=normalized,
            description=description,
            capabilities=set(capabilities),
            priority=priority,
            readiness=readiness,
            metadata=dict(metadata or {}),
        )

    def unregister(self, name: str) -> None:
        normalized = normalize_director_name(name)
        self._handlers.pop(normalized, None)
        self._descriptors.pop(normalized, None)

    def resolve(self, name: str) -> DirectorHandler:
        normalized = normalize_director_name(name)
        try:
            return self._handlers[normalized]
        except KeyError as exc:
            raise DirectorNotRegisteredError(
                f"No director registered for '{normalized}'"
            ) from exc

    def descriptor(self, name: str) -> DirectorDescriptor:
        normalized = normalize_director_name(name)
        try:
            return self._descriptors[normalized]
        except KeyError as exc:
            raise DirectorNotRegisteredError(
                f"No descriptor registered for '{normalized}'"
            ) from exc

    def descriptors(self) -> tuple[DirectorDescriptor, ...]:
        return tuple(self._descriptors[name] for name in sorted(self._descriptors))

    def names(self) -> tuple[str, ...]:
        return tuple(sorted(self._handlers))

    def contains(self, name: str) -> bool:
        return normalize_director_name(name) in self._handlers

    def require(self, names: Iterable[str]) -> None:
        missing = [name for name in names if not self.contains(name)]
        if missing:
            raise DirectorNotRegisteredError(
                "Missing required directors: " + ", ".join(sorted(missing))
            )

    def set_readiness(self, name: str, readiness: DirectorReadiness) -> None:
        normalized = normalize_director_name(name)
        self._descriptors[normalized] = replace(
            self.descriptor(normalized),
            readiness=readiness,
        )

    def select(
        self,
        required_capabilities: Iterable[str],
        *,
        fallback: str = "executive",
    ) -> RoutingDecision:
        required = tuple(sorted({normalize_capability(c) for c in required_capabilities}))
        if not required:
            selected = normalize_director_name(fallback)
            self.resolve(selected)
            return RoutingDecision(
                selected_director=selected,
                required_capabilities=(),
                candidates=(),
                reason="No specialist capabilities were required.",
            )

        required_set = set(required)
        candidates: list[RoutingCandidate] = []

        for descriptor in self.descriptors():
            matched = tuple(sorted(required_set & descriptor.capabilities))
            missing = tuple(sorted(required_set - descriptor.capabilities))
            coverage = len(matched) / len(required)
            readiness_weight = {
                DirectorReadiness.READY: 1.0,
                DirectorReadiness.DEGRADED: 0.65,
                DirectorReadiness.UNAVAILABLE: 0.0,
            }[descriptor.readiness]
            priority_bonus = max(0.0, (1000 - descriptor.priority) / 100000)
            score = round((coverage * readiness_weight) + priority_bonus, 6)
            candidates.append(
                RoutingCandidate(
                    director=descriptor.name,
                    matched_capabilities=matched,
                    missing_capabilities=missing,
                    score=score,
                    priority=descriptor.priority,
                    readiness=descriptor.readiness,
                )
            )

        viable = [
            candidate
            for candidate in candidates
            if candidate.readiness != DirectorReadiness.UNAVAILABLE
            and candidate.matched_capabilities
        ]

        if viable:
            viable.sort(
                key=lambda candidate: (
                    -candidate.score,
                    len(candidate.missing_capabilities),
                    candidate.priority,
                    candidate.director,
                )
            )
            selected = viable[0]
            reason = (
                f"Selected '{selected.director}' with "
                f"{len(selected.matched_capabilities)}/{len(required)} "
                "required capabilities matched."
            )
        else:
            fallback_name = normalize_director_name(fallback)
            self.resolve(fallback_name)
            descriptor = self.descriptor(fallback_name)
            selected = RoutingCandidate(
                director=fallback_name,
                matched_capabilities=(),
                missing_capabilities=required,
                score=0.0,
                priority=descriptor.priority,
                readiness=descriptor.readiness,
            )
            reason = (
                "No ready specialist matched the required capabilities; "
                f"fell back to '{fallback_name}'."
            )

        ranked = tuple(
            sorted(
                candidates,
                key=lambda candidate: (
                    -candidate.score,
                    candidate.priority,
                    candidate.director,
                ),
            )
        )
        return RoutingDecision(
            selected_director=selected.director,
            required_capabilities=required,
            candidates=ranked,
            reason=reason,
        )
