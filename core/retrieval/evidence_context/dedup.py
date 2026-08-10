from __future__ import annotations

import hashlib
import re

WS = re.compile(r"\s+")
PUNCT = re.compile(r"[^\w+#]+", re.UNICODE)


def normalize(text: str) -> str:
    text = text.casefold()
    text = PUNCT.sub(" ", text)
    return WS.sub(" ", text).strip()


def evidence_fingerprint(text: str) -> str:
    return hashlib.sha256(normalize(text).encode("utf-8", errors="ignore")).hexdigest()


def overlap_ratio(a: str, b: str) -> float:
    aa = set(normalize(a).split())
    bb = set(normalize(b).split())
    if not aa or not bb:
        return 0.0
    return len(aa & bb) / min(len(aa), len(bb))
