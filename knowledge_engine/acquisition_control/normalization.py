"""
Deterministic source normalization for JARVIS Phase VII-B1.

Normalization is intentionally side-effect free. Local paths are normalized
lexically and are not required to exist.
"""

from __future__ import annotations

import hashlib
import json
import posixpath
import re
from pathlib import Path, PurePath
from typing import Any
from urllib.parse import (
    parse_qsl,
    quote,
    urlencode,
    urlsplit,
    urlunsplit,
)

from .contracts import (
    AdmissionDecision,
    AdmissionReason,
    AdmissionStatus,
    NormalizedSource,
    SourceKind,
    SourceProposal,
)


_SOURCE_ID_PATTERN = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._:-]{0,127}$")


class SourceNormalizationError(ValueError):
    """Raised when a source proposal cannot be normalized."""

    def __init__(
        self,
        reason: AdmissionReason,
        message: str,
        *,
        diagnostics: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.reason = reason
        self.message = message
        self.diagnostics = dict(diagnostics or {})

    def to_decision(self) -> AdmissionDecision:
        """Convert the exception to a stable rejection decision."""

        return AdmissionDecision(
            status=AdmissionStatus.REJECTED,
            reason=self.reason,
            message=self.message,
            diagnostics=self.diagnostics,
        )


def _validate_identity(proposal: SourceProposal) -> tuple[str, str]:
    source_id = proposal.source_id.strip()
    display_name = " ".join(proposal.display_name.split())

    if not source_id or not _SOURCE_ID_PATTERN.fullmatch(source_id):
        raise SourceNormalizationError(
            AdmissionReason.INVALID_SOURCE_ID,
            (
                "source_id must contain 1-128 letters, numbers, periods, "
                "underscores, colons, or hyphens and must begin with an "
                "alphanumeric character"
            ),
            diagnostics={"source_id": proposal.source_id},
        )

    if not display_name or len(display_name) > 200:
        raise SourceNormalizationError(
            AdmissionReason.INVALID_DISPLAY_NAME,
            "display_name must contain 1-200 visible characters",
        )

    return source_id, display_name


def _canonicalize_https(location: str) -> tuple[str, str]:
    raw = location.strip()

    try:
        parsed = urlsplit(raw)
    except ValueError as exc:
        raise SourceNormalizationError(
            AdmissionReason.INVALID_LOCATION,
            f"Invalid source URL: {exc}",
        ) from exc

    if parsed.scheme.lower() != "https":
        raise SourceNormalizationError(
            AdmissionReason.UNSUPPORTED_SCHEME,
            "Only HTTPS network sources are supported",
            diagnostics={"scheme": parsed.scheme.lower()},
        )

    if parsed.username is not None or parsed.password is not None:
        raise SourceNormalizationError(
            AdmissionReason.URL_CREDENTIALS_FORBIDDEN,
            "Credentials must not be embedded in source URLs",
        )

    host = (parsed.hostname or "").lower().rstrip(".")
    if not host:
        raise SourceNormalizationError(
            AdmissionReason.INVALID_LOCATION,
            "HTTPS source must include a hostname",
        )

    try:
        port = parsed.port
    except ValueError as exc:
        raise SourceNormalizationError(
            AdmissionReason.INVALID_LOCATION,
            f"Invalid URL port: {exc}",
        ) from exc

    netloc = host
    if port is not None and port != 443:
        netloc = f"{host}:{port}"

    raw_path = parsed.path or "/"
    normalized_path = posixpath.normpath(raw_path)

    if not normalized_path.startswith("/"):
        normalized_path = f"/{normalized_path}"

    if raw_path.endswith("/") and not normalized_path.endswith("/"):
        normalized_path = f"{normalized_path}/"

    if normalized_path == "//":
        normalized_path = "/"

    encoded_path = quote(normalized_path, safe="/:@-._~!$&'()*+,;=")

    sorted_query = sorted(
        parse_qsl(parsed.query, keep_blank_values=True),
        key=lambda item: (item[0], item[1]),
    )
    canonical_query = urlencode(sorted_query, doseq=True)

    canonical = urlunsplit(
        (
            "https",
            netloc,
            encoded_path,
            canonical_query,
            "",
        )
    )

    return canonical, host


def _canonicalize_local_path(location: str) -> str:
    raw = location.strip()

    if not raw:
        raise SourceNormalizationError(
            AdmissionReason.INVALID_LOCATION,
            "Local source path must not be empty",
        )

    if "\x00" in raw:
        raise SourceNormalizationError(
            AdmissionReason.INVALID_LOCATION,
            "Local source path contains a null byte",
        )

    expanded = Path(raw).expanduser()

    try:
        canonical = str(expanded.resolve(strict=False))
    except (OSError, RuntimeError) as exc:
        raise SourceNormalizationError(
            AdmissionReason.INVALID_LOCATION,
            f"Unable to normalize local path: {exc}",
        ) from exc

    return canonical


def build_source_fingerprint(
    *,
    source_id: str,
    canonical_location: str,
    kind: SourceKind,
    trust_tier: str,
) -> str:
    """Build a deterministic SHA-256 source identity fingerprint."""

    payload = {
        "canonical_location": canonical_location,
        "kind": kind.value,
        "source_id": source_id,
        "trust_tier": trust_tier,
    }
    serialized = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def normalize_source(proposal: SourceProposal) -> NormalizedSource:
    """
    Validate and normalize an untrusted source proposal.

    This function performs no admission-policy decision.
    """

    if not isinstance(proposal, SourceProposal):
        raise TypeError("proposal must be a SourceProposal")

    source_id, display_name = _validate_identity(proposal)

    if not isinstance(proposal.location, str):
        raise SourceNormalizationError(
            AdmissionReason.INVALID_LOCATION,
            "location must be a string",
        )

    if proposal.kind is SourceKind.HTTPS:
        canonical_location, host = _canonicalize_https(proposal.location)
    elif proposal.kind in {
        SourceKind.LOCAL_FILE,
        SourceKind.LOCAL_DIRECTORY,
    }:
        canonical_location = _canonicalize_local_path(proposal.location)
        host = None
    else:
        raise SourceNormalizationError(
            AdmissionReason.UNSUPPORTED_SCHEME,
            f"Unsupported source kind: {proposal.kind!r}",
        )

    fingerprint = build_source_fingerprint(
        source_id=source_id,
        canonical_location=canonical_location,
        kind=proposal.kind,
        trust_tier=proposal.trust_tier.value,
    )

    return NormalizedSource(
        source_id=source_id,
        display_name=display_name,
        canonical_location=canonical_location,
        kind=proposal.kind,
        trust_tier=proposal.trust_tier,
        fingerprint=fingerprint,
        host=host,
        metadata=proposal.metadata,
    )


def is_within_root(path: str, root: str) -> bool:
    """
    Return whether path is equal to or lexically contained by root.

    Both paths are normalized without requiring filesystem existence.
    """

    candidate = Path(path).resolve(strict=False)
    allowed_root = Path(root).expanduser().resolve(strict=False)

    try:
        candidate.relative_to(allowed_root)
    except ValueError:
        return False

    return True


def path_components(path: str) -> tuple[str, ...]:
    """Expose normalized path components for diagnostics and testing."""

    return tuple(PurePath(path).parts)
