from __future__ import annotations

import hashlib
import re


WS = re.compile(r"\s+")
PUNCT = re.compile(r"[^\w+#]+", re.UNICODE)


def normalize_text(text: str) -> str:
    text = text.casefold()
    text = PUNCT.sub(" ", text)
    return WS.sub(" ", text).strip()


def duplicate_key(text: str) -> str:
    n = normalize_text(text)
    return hashlib.sha256(n.encode("utf-8", errors="ignore")).hexdigest()


def path_family(path: str) -> str:
    p = str(path).replace("\\", "/").casefold()
    parts = [x for x in p.split("/") if x]
    # Keep filename + immediate parent. This is enough to identify repeated
    # library copies without collapsing unrelated books with similar titles.
    tail = "/".join(parts[-2:])
    return tail
