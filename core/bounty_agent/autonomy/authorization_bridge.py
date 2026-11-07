"""R9.14B: read-only candidate-to-authorization matching.

This module never creates authorizations or launches tools.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Candidate:
    program: str
    target: str
    score: float = 0.0


@dataclass(frozen=True)
class AuthorizationBinding:
    authorization_id: str
    program: str
    target: str
    reviewed: bool
    active: bool


def select_authorized_candidate(
    candidates,
    bindings,
    *,
    scope_store,
):
    """Select a candidate using independently reviewed scope."""
    ordered = sorted(
        candidates,
        key=lambda item: (-item.score, item.program, item.target),
    )

    for candidate in ordered:
        for binding in bindings:
            if not binding.reviewed or not binding.active:
                continue

            if binding.program != candidate.program:
                continue

            if binding.target != candidate.target:
                continue

            try:
                scope = scope_store.live_scope(
                    binding.authorization_id
                )

                if scope.program != candidate.program:
                    continue

                if not scope.permits_host(candidate.target):
                    continue

                if not (
                    "subdomain_discovery"
                    in scope.logical_capabilities
                    or "dns_resolution"
                    in scope.logical_capabilities
                ):
                    continue

                scope.require(
                    candidate.target,
                    (
                        "subfinder"
                        if "subdomain_discovery"
                        in scope.logical_capabilities
                        else "dnsx"
                    ),
                )

            except (ValueError, KeyError):
                continue

            return {
                "status": "authorized_candidate_selected",
                "program": candidate.program,
                "target": candidate.target,
                "authorization_id": binding.authorization_id,
                "execution_started": False,
            }

    return {
        "status": "no_authorized_candidate",
        "execution_started": False,
    }
