from __future__ import annotations

def is_context_overflow(detail: str) -> bool:
    d=(detail or "").casefold()
    return (
        "input length exceeds the context length" in d
        or "context length" in d
        or "too many tokens" in d
    )
