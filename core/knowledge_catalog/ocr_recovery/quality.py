from __future__ import annotations
import math
import re

WORD_RE = re.compile(r"[A-Za-zÀ-ÖØ-öø-ÿ\u0600-\u06ff]{2,}")
PRINTABLE_RE = re.compile(r"[\w\s.,;:!?()\[\]{}'\"/\\+\-=%$#@&*<>|~`^]", re.UNICODE)

def quality_score(text: str) -> float:
    value = text or ""
    stripped = value.strip()
    if not stripped:
        return 0.0

    total = max(1, len(value))
    printable = sum(1 for ch in value if ch.isprintable() or ch in "\n\t")
    printable_ratio = printable / total

    words = WORD_RE.findall(value)
    word_chars = sum(len(w) for w in words)
    lexical_ratio = min(1.0, word_chars / max(1, len(stripped)))

    replacements = value.count("\ufffd")
    replacement_penalty = min(1.0, replacements / max(1, total // 100))

    line_lengths = [len(x.strip()) for x in value.splitlines() if x.strip()]
    if line_lengths:
        avg = sum(line_lengths) / len(line_lengths)
        line_score = 1.0 if 8 <= avg <= 180 else max(0.0, 1.0 - abs(avg - 60) / 180)
    else:
        line_score = 0.0

    score = (
        0.35 * printable_ratio
        + 0.40 * lexical_ratio
        + 0.25 * line_score
        - 0.25 * replacement_penalty
    )
    return max(0.0, min(1.0, score))
