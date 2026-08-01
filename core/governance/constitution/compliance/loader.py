from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .contracts import APPLICABLE_ARTICLE_STATUSES
from .models import ArticleReference, ChangeSubject


class ComplianceArtifactError(RuntimeError):
    pass


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ComplianceArtifactError(f"Missing artifact: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ComplianceArtifactError(f"Invalid JSON artifact: {path}: {exc}") from exc


def load_ratification(
    directory: Path,
    require_ratified_only: bool,
) -> tuple[str, str, str, str, tuple[ArticleReference, ...]]:
    summary = _read_json(directory / "constitutional_ratification.json")
    registry = _read_json(directory / "constitutional_registry.json")

    raw_articles = registry.get("articles", [])
    if not isinstance(raw_articles, list):
        raise ComplianceArtifactError("constitutional_registry.json must contain an articles list")

    articles: list[ArticleReference] = []
    for index, item in enumerate(raw_articles):
        if not isinstance(item, dict):
            raise ComplianceArtifactError(f"Article at index {index} is not an object")
        status = str(item.get("status", ""))
        if require_ratified_only and status != "ratified":
            continue
        if not require_ratified_only and status not in APPLICABLE_ARTICLE_STATUSES:
            continue
        article = ArticleReference(
            article_id=str(item.get("article_id", "")),
            canonical_text=str(item.get("canonical_text", "")),
            domain=str(item.get("domain", "general") or "general"),
            status=status,
            authority=str(item.get("authority", "other") or "other"),
            authority_rank=int(item.get("authority_rank", 100) or 100),
            fingerprint=str(item.get("fingerprint", "")),
        )
        if not article.article_id or not article.canonical_text:
            raise ComplianceArtifactError(f"Article at index {index} lacks article_id or canonical_text")
        articles.append(article)

    articles.sort(key=lambda item: item.article_id)
    return (
        str(summary.get("repository_fingerprint", "")),
        str(summary.get("extraction_fingerprint", "")),
        str(summary.get("analysis_fingerprint", "")),
        str(summary.get("ratification_fingerprint", "")),
        tuple(articles),
    )


def load_subjects(path: Path) -> tuple[ChangeSubject, ...]:
    payload = _read_json(path)
    raw_subjects = payload.get("subjects", payload if isinstance(payload, list) else [])
    if not isinstance(raw_subjects, list):
        raise ComplianceArtifactError("Compliance subject input must be a list or {'subjects': [...]}")

    subjects: list[ChangeSubject] = []
    for index, item in enumerate(raw_subjects):
        if not isinstance(item, dict):
            raise ComplianceArtifactError(f"Subject at index {index} is not an object")
        subject_id = str(item.get("subject_id", item.get("id", "")))
        content = str(item.get("content", item.get("text", "")))
        if not subject_id or not content:
            raise ComplianceArtifactError(f"Subject at index {index} lacks subject_id or content")
        basis = {
            "subject_id": subject_id,
            "subject_type": str(item.get("subject_type", "document")),
            "path": str(item.get("path", "")),
            "title": str(item.get("title", subject_id)),
            "content": content,
            "domain": str(item.get("domain", "general") or "general"),
        }
        fingerprint = hashlib.sha256(
            json.dumps(
                basis,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
            ).encode("utf-8")
        ).hexdigest()
        subjects.append(ChangeSubject(fingerprint=fingerprint, **basis))

    subjects.sort(key=lambda item: item.subject_id)
    return tuple(subjects)
