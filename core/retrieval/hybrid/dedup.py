from __future__ import annotations
import hashlib, re
from pathlib import Path

SPACE_RE = re.compile(r"\s+")

def normalize_title(title: str) -> str:
    t = Path(title or "").stem.casefold()
    t = re.sub(r"[^a-z0-9\u0600-\u06ff]+", " ", t)
    return SPACE_RE.sub(" ", t).strip()

def duplicate_key(title: str, excerpt: str) -> str:
    # Intentionally conservative: collapse obvious duplicate editions/copies without
    # pretending distinct documents are identical.
    nt = normalize_title(title)
    sample = SPACE_RE.sub(" ", (excerpt or "").casefold()).strip()[:300]
    base = nt if nt else sample
    return hashlib.sha1(base.encode("utf-8", errors="ignore")).hexdigest()
