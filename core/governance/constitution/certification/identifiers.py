from __future__ import annotations

import hashlib


def stable_identifier(prefix: str, payload: str, length: int = 20) -> str:
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest().upper()
    return f"{prefix}-{digest[:length]}"
