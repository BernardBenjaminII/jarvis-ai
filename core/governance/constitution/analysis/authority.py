from __future__ import annotations

from pathlib import PurePosixPath

from .contracts import AUTHORITY_RANK, AuthorityLevel


def classify_authority(path: str) -> AuthorityLevel:
    p = path.lower()
    name = PurePosixPath(path).name.lower()

    if "/constitution/" in f"/{p}" or "constitution" in name:
        if "engineering_constitution" in name or "engineering-constitution" in name:
            return AuthorityLevel.ENGINEERING_CONSTITUTION
        return AuthorityLevel.CONSTITUTION
    if "/policy/" in f"/{p}" or "/policies/" in f"/{p}" or "policy" in name:
        return AuthorityLevel.POLICY
    if "adr-" in name or "/decisions/" in f"/{p}":
        return AuthorityLevel.ADR
    if "/architecture/" in f"/{p}" or "architecture" in name:
        return AuthorityLevel.ARCHITECTURE
    if "/whitepapers/" in f"/{p}" or "whitepaper" in name or name.startswith("wp-"):
        return AuthorityLevel.WHITEPAPER
    return AuthorityLevel.OTHER


def authority_rank(level: AuthorityLevel) -> int:
    return AUTHORITY_RANK[level]


def resolve_authority(left_rank: int, right_rank: int, left_id: str, right_id: str) -> str:
    if left_rank > right_rank:
        return left_id
    if right_rank > left_rank:
        return right_id
    return "unresolved_equal_authority"
