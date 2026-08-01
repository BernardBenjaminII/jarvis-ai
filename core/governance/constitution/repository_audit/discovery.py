from __future__ import annotations

import re
from pathlib import Path

from .fingerprints import canonical_fingerprint, text_fingerprint
from .models import RepositoryArtifact, RepositoryAuditPolicy


class RepositoryAuditDiscoveryError(RuntimeError):
    pass


def _artifact_type(path: Path) -> str:
    relative = path.as_posix().lower()
    name = path.name.lower()

    if "docs/decisions/" in relative or name.startswith("adr-"):
        return "architecture_decision"
    if "constitution" in name or "/constitution/" in relative:
        return "constitution"
    if "whitepaper" in relative or name.startswith("wp-"):
        return "whitepaper"
    if "architecture" in relative:
        return "architecture_document"
    if "mission" in relative:
        return "mission_document"
    if path.suffix.lower() in {".yaml", ".yml", ".toml", ".json"}:
        return "configuration"
    if path.suffix.lower() in {".py", ".sh", ".js", ".jsx", ".ts", ".tsx"}:
        return "source_code"
    return "document"


def _domain(path: Path, content: str) -> str:
    lowered = f"{path.as_posix()} {content[:1000]}".lower()
    candidates = (
        "governance",
        "security",
        "knowledge",
        "reasoning",
        "memory",
        "planning",
        "execution",
        "engineering",
        "architecture",
        "experience",
        "executive",
    )
    for candidate in candidates:
        if re.search(rf"\b{re.escape(candidate)}\b", lowered):
            return candidate
    return "general"


def discover_repository_artifacts(
    repository_root: Path,
    policy: RepositoryAuditPolicy,
) -> tuple[RepositoryArtifact, ...]:
    root = repository_root.resolve()
    if not root.is_dir():
        raise RepositoryAuditDiscoveryError(
            f"Repository root does not exist or is not a directory: {root}"
        )

    artifacts: list[RepositoryArtifact] = []
    excluded = set(policy.excluded_directories)
    allowed_suffixes = set(policy.included_suffixes)

    for path in sorted(root.rglob("*"), key=lambda item: item.as_posix()):
        if not path.is_file():
            continue

        relative = path.relative_to(root)
        if any(part in excluded for part in relative.parts[:-1]):
            continue
        if path.suffix.lower() not in allowed_suffixes:
            continue

        size = path.stat().st_size
        if size == 0 or size > policy.maximum_file_bytes:
            continue

        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue

        relative_path = relative.as_posix()
        content_hash = text_fingerprint(content)
        identity_basis = {
            "path": relative_path,
            "content_fingerprint": content_hash,
            "artifact_type": _artifact_type(relative),
        }
        artifact_id = f"RA-{canonical_fingerprint(identity_basis)[:20].upper()}"

        artifacts.append(
            RepositoryArtifact(
                artifact_id=artifact_id,
                path=relative_path,
                artifact_type=identity_basis["artifact_type"],
                suffix=path.suffix.lower(),
                size_bytes=size,
                content_fingerprint=content_hash,
                content=content,
                domain=_domain(relative, content),
            )
        )

    artifacts.sort(key=lambda item: (item.path, item.artifact_id))
    return tuple(artifacts)
