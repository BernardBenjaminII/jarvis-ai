"""Deterministic identifiers for constitutional cognition objects."""

from __future__ import annotations

import re
from typing import Any

from .enums import CognitiveObjectKind
from .errors import CognitionIdentifierError
from .serialization import canonical_fingerprint

_IDENTIFIER_PATTERN = re.compile(
    r"^cog_(?P<kind>[a-z][a-z0-9_]*)_(?P<digest>[0-9a-f]{32})$"
)


def normalize_kind(kind: CognitiveObjectKind | str) -> str:
    """Normalize and validate a cognitive object kind."""

    value = kind.value if isinstance(kind, CognitiveObjectKind) else str(kind)
    value = value.strip().lower()

    try:
        return CognitiveObjectKind(value).value
    except ValueError as exc:
        raise CognitionIdentifierError(
            f"Unsupported cognitive object kind: {value!r}"
        ) from exc


def make_cognition_id(
    kind: CognitiveObjectKind | str,
    identity_payload: Any,
) -> str:
    """Create a deterministic cognition identifier from canonical identity data."""

    normalized_kind = normalize_kind(kind)
    digest = canonical_fingerprint(identity_payload)[:32]
    return f"cog_{normalized_kind}_{digest}"


def parse_cognition_id(identifier: str) -> tuple[CognitiveObjectKind, str]:
    """Parse and validate a cognition identifier."""

    if not isinstance(identifier, str):
        raise CognitionIdentifierError("Cognition identifiers must be strings.")

    match = _IDENTIFIER_PATTERN.fullmatch(identifier)

    if match is None:
        raise CognitionIdentifierError(
            f"Invalid cognition identifier: {identifier!r}"
        )

    raw_kind = match.group("kind")

    try:
        kind = CognitiveObjectKind(raw_kind)
    except ValueError as exc:
        raise CognitionIdentifierError(
            f"Identifier contains unsupported cognition kind: {raw_kind!r}"
        ) from exc

    return kind, match.group("digest")


def validate_cognition_id(
    identifier: str,
    expected_kind: CognitiveObjectKind | str | None = None,
) -> None:
    """Validate an identifier and optionally enforce its object kind."""

    actual_kind, _ = parse_cognition_id(identifier)

    if expected_kind is None:
        return

    normalized_expected = CognitiveObjectKind(normalize_kind(expected_kind))

    if actual_kind is not normalized_expected:
        raise CognitionIdentifierError(
            f"Expected {normalized_expected.value!r} identifier, "
            f"received {actual_kind.value!r}."
        )


def verify_cognition_id(
    identifier: str,
    kind: CognitiveObjectKind | str,
    identity_payload: Any,
) -> None:
    """Verify that an identifier matches its canonical identity payload."""

    expected = make_cognition_id(kind, identity_payload)

    if identifier != expected:
        raise CognitionIdentifierError(
            f"Identifier does not match canonical identity. "
            f"Expected {expected!r}, received {identifier!r}."
        )
