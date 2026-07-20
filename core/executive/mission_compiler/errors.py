"""Errors raised by the deterministic JARVIS Mission Compiler."""

from __future__ import annotations


class MissionCompilationError(RuntimeError):
    """Base error for mission compilation failures."""


class EmptyMissionPlanError(MissionCompilationError):
    """Raised when a planning mission contains no executable commands."""


class DuplicatePlanElementError(MissionCompilationError):
    """Raised when a planning hierarchy contains duplicate element IDs."""


class UnsupportedDependencyError(MissionCompilationError):
    """Raised when a dependency cannot be lowered without losing meaning."""


class UnknownDependencyElementError(MissionCompilationError):
    """Raised when a dependency references an unknown plan element."""


class CyclicRuntimeDependencyError(MissionCompilationError):
    """Raised when lowered runtime dependencies contain a cycle."""
