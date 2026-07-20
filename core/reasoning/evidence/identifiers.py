"""Deterministic identifiers for Genesis II-A4 Evidence contracts."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, ClassVar, TypeVar

from .errors import EvidenceIdentityError
from .serialization import canonical_sha256

_HEX_DIGEST = re.compile(r"^[0-9a-f]{64}$")

IdentifierT = TypeVar("IdentifierT", bound="CanonicalEvidenceIdentifier")


@dataclass(frozen=True, slots=True, order=True)
class CanonicalEvidenceIdentifier:
    """Base deterministic identifier represented as ``prefix:sha256``."""

    value: str

    PREFIX: ClassVar[str] = "evidence-id"

    def __post_init__(self) -> None:
        expected_prefix = f"{self.PREFIX}:"

        if not isinstance(self.value, str):
            raise EvidenceIdentityError("identifier value must be a string")

        if not self.value.startswith(expected_prefix):
            raise EvidenceIdentityError(
                f"identifier must begin with {expected_prefix!r}"
            )

        digest = self.value[len(expected_prefix):]

        if not _HEX_DIGEST.fullmatch(digest):
            raise EvidenceIdentityError(
                "identifier digest must be 64 lowercase hexadecimal characters"
            )

    @classmethod
    def from_payload(
        cls: type[IdentifierT],
        payload: Any,
        *,
        identity_version: str = "1",
    ) -> IdentifierT:
        """Create an identifier from canonical payload content."""

        digest = canonical_sha256(
            {
                "identity_type": cls.PREFIX,
                "identity_version": identity_version,
                "payload": payload,
            }
        )
        return cls(f"{cls.PREFIX}:{digest}")

    @classmethod
    def parse(cls: type[IdentifierT], value: str) -> IdentifierT:
        return cls(value)

    def canonical_value(self) -> str:
        return self.value

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True, order=True)
class EvidenceContentId(CanonicalEvidenceIdentifier):
    """Identity of normalized Evidence content."""

    PREFIX: ClassVar[str] = "evidence-content"


@dataclass(frozen=True, slots=True, order=True)
class EvidenceId(CanonicalEvidenceIdentifier):
    """Identity of a canonical Evidence record."""

    PREFIX: ClassVar[str] = "evidence"


@dataclass(frozen=True, slots=True, order=True)
class EvidenceAssessmentId(CanonicalEvidenceIdentifier):
    """Identity of a contextual Evidence assessment."""

    PREFIX: ClassVar[str] = "evidence-assessment"


@dataclass(frozen=True, slots=True, order=True)
class EvidenceStatusEventId(CanonicalEvidenceIdentifier):
    """Identity of an append-only Evidence standing event."""

    PREFIX: ClassVar[str] = "evidence-status-event"


@dataclass(frozen=True, slots=True, order=True)
class EvidenceRelationshipId(CanonicalEvidenceIdentifier):
    """Identity of a typed Evidence relationship."""

    PREFIX: ClassVar[str] = "evidence-relationship"
