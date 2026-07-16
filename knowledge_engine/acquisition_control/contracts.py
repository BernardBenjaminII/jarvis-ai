"""
Immutable contracts for JARVIS acquisition source admission.

Phase VII-B1 establishes the boundary between an untrusted source proposal
and the frozen acquisition subsystem.

This module performs no network access, filesystem mutation, catalog writes,
or acquisition execution.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping


class SourceKind(str, Enum):
    """Supported source-address families."""

    HTTPS = "https"
    LOCAL_FILE = "local_file"
    LOCAL_DIRECTORY = "local_directory"


class SourceTrustTier(str, Enum):
    """
    Declared source trust classification.

    Trust is policy input, not proof that a source is factually correct.
    """

    OFFICIAL = "official"
    INSTITUTIONAL = "institutional"
    COMMUNITY = "community"
    UNKNOWN = "unknown"
    RESTRICTED = "restricted"


class AdmissionStatus(str, Enum):
    """Possible source-admission outcomes."""

    ACCEPTED = "accepted"
    REVIEW_REQUIRED = "review_required"
    REJECTED = "rejected"


class AdmissionReason(str, Enum):
    """Stable machine-readable admission reason codes."""

    ACCEPTED_BY_POLICY = "accepted_by_policy"
    MANUAL_REVIEW_REQUIRED = "manual_review_required"
    INVALID_SOURCE_ID = "invalid_source_id"
    INVALID_DISPLAY_NAME = "invalid_display_name"
    INVALID_LOCATION = "invalid_location"
    UNSUPPORTED_SCHEME = "unsupported_scheme"
    URL_CREDENTIALS_FORBIDDEN = "url_credentials_forbidden"
    NETWORK_SOURCE_DISABLED = "network_source_disabled"
    LOCAL_SOURCE_DISABLED = "local_source_disabled"
    RESTRICTED_SOURCE = "restricted_source"
    UNKNOWN_TRUST_REQUIRES_REVIEW = "unknown_trust_requires_review"
    COMMUNITY_SOURCE_REQUIRES_REVIEW = "community_source_requires_review"
    HOST_NOT_ALLOWED = "host_not_allowed"
    HOST_BLOCKED = "host_blocked"
    PATH_OUTSIDE_ALLOWED_ROOTS = "path_outside_allowed_roots"


def _immutable_mapping(
    value: Mapping[str, Any] | None,
) -> Mapping[str, Any]:
    """Return a shallow immutable copy of mapping metadata."""

    return MappingProxyType(dict(value or {}))


@dataclass(frozen=True, slots=True)
class SourceProposal:
    """
    Untrusted proposal submitted for acquisition admission.

    source_id:
        Stable caller-provided identifier.

    display_name:
        Human-readable source name.

    location:
        HTTPS URL or local path.

    kind:
        Declared source family.

    trust_tier:
        Caller-declared trust classification.

    metadata:
        Non-authoritative supplemental information.
    """

    source_id: str
    display_name: str
    location: str
    kind: SourceKind
    trust_tier: SourceTrustTier = SourceTrustTier.UNKNOWN
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", _immutable_mapping(self.metadata))


@dataclass(frozen=True, slots=True)
class NormalizedSource:
    """Canonical source representation produced after structural validation."""

    source_id: str
    display_name: str
    canonical_location: str
    kind: SourceKind
    trust_tier: SourceTrustTier
    fingerprint: str
    host: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", _immutable_mapping(self.metadata))


@dataclass(frozen=True, slots=True)
class AdmissionDecision:
    """Immutable result of evaluating one source proposal."""

    status: AdmissionStatus
    reason: AdmissionReason
    message: str
    source: NormalizedSource | None = None
    diagnostics: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "diagnostics",
            _immutable_mapping(self.diagnostics),
        )

    @property
    def accepted(self) -> bool:
        """Return true only for fully admitted sources."""

        return self.status is AdmissionStatus.ACCEPTED

    @property
    def requires_review(self) -> bool:
        """Return true when human approval is required."""

        return self.status is AdmissionStatus.REVIEW_REQUIRED

    @property
    def rejected(self) -> bool:
        """Return true when policy rejects the proposal."""

        return self.status is AdmissionStatus.REJECTED


@dataclass(frozen=True, slots=True)
class AdmissionPolicy:
    """
    Immutable source-admission policy.

    Network and local sources are independently controlled. Host allowlists
    and blocklists apply only to HTTPS sources. Allowed roots apply only to
    local paths.
    """

    allow_network_sources: bool = True
    allow_local_sources: bool = True
    review_unknown_sources: bool = True
    review_community_sources: bool = True
    allowed_hosts: frozenset[str] = field(default_factory=frozenset)
    blocked_hosts: frozenset[str] = field(default_factory=frozenset)
    allowed_local_roots: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        normalized_allowed_hosts = frozenset(
            host.strip().lower().rstrip(".")
            for host in self.allowed_hosts
            if host.strip()
        )
        normalized_blocked_hosts = frozenset(
            host.strip().lower().rstrip(".")
            for host in self.blocked_hosts
            if host.strip()
        )
        normalized_roots = tuple(
            root.strip()
            for root in self.allowed_local_roots
            if root.strip()
        )

        object.__setattr__(
            self,
            "allowed_hosts",
            normalized_allowed_hosts,
        )
        object.__setattr__(
            self,
            "blocked_hosts",
            normalized_blocked_hosts,
        )
        object.__setattr__(
            self,
            "allowed_local_roots",
            normalized_roots,
        )
