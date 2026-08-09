"""Canonical JSON primitives used by the Government Framework."""

from __future__ import annotations

from hashlib import sha256
import json
from typing import Any, Mapping


def canonical_json(payload: Mapping[str, Any]) -> str:
    """Return deterministic UTF-8-safe JSON with stable key ordering."""

    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    )


def canonical_bytes(payload: Mapping[str, Any]) -> bytes:
    return canonical_json(payload).encode("utf-8")


def canonical_fingerprint(payload: Mapping[str, Any]) -> str:
    return sha256(canonical_bytes(payload)).hexdigest()
