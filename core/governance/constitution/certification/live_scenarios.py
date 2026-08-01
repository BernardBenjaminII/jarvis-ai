from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from core.governance.constitution.compliance.models import ArticleReference
from core.governance.constitution.compliance.normalize import polarity, token_set

from .contracts import ScenarioKind
from .fingerprints import canonical_fingerprint
from .identifiers import stable_identifier
from .models import LiveCertificationScenario


class LiveScenarioGenerationError(RuntimeError):
    pass


_NEGATIVE_MARKERS = (
    "must not",
    "shall not",
    "should not",
    "may not",
    "never",
    "prohibited",
    "forbidden",
    "cannot",
)


def select_certification_article(
    articles: Iterable[ArticleReference],
) -> ArticleReference:
    eligible = [
        article
        for article in articles
        if article.status == "ratified"
        and len(token_set(article.canonical_text)) >= 8
        and article.article_id
        and article.fingerprint
    ]
    if not eligible:
        raise LiveScenarioGenerationError(
            "No ratified constitutional article with at least eight normalized tokens "
            "is available for live scenario generation."
        )

    eligible.sort(
        key=lambda article: (
            -len(token_set(article.canonical_text)),
            article.authority_rank,
            article.article_id,
        )
    )
    return eligible[0]


def invert_normative_polarity(text: str) -> str:
    lowered = text.lower()
    if polarity(text) < 0:
        transformed = text
        for marker in _NEGATIVE_MARKERS:
            index = transformed.lower().find(marker)
            if index >= 0:
                transformed = (
                    transformed[:index]
                    + marker.replace(" not", "").replace("never", "always")
                    .replace("prohibited", "required")
                    .replace("forbidden", "required")
                    .replace("cannot", "must")
                    + transformed[index + len(marker):]
                )
                break
        return transformed

    return f"Must not {text}"


def build_review_content(text: str) -> str:
    normalized_tokens = sorted(token_set(text))
    if len(normalized_tokens) < 8:
        raise LiveScenarioGenerationError(
            "Review scenario requires an article with at least eight normalized tokens."
        )

    target_count = max(3, min(len(normalized_tokens) - 1, len(normalized_tokens) // 2))
    selected = normalized_tokens[:target_count]
    return " ".join(selected)


def _scenario(
    *,
    kind: str,
    title: str,
    expected_status: str,
    article: ArticleReference | None,
    subject_content: str,
    subject_domain: str,
) -> LiveCertificationScenario:
    expected_article_id = article.article_id if article else ""
    source_article_fingerprint = article.fingerprint if article else ""
    subject_basis = {
        "kind": kind,
        "expected_status": expected_status,
        "expected_article_id": expected_article_id,
        "subject_content": subject_content,
        "subject_domain": subject_domain,
        "source_article_fingerprint": source_article_fingerprint,
    }
    fingerprint = canonical_fingerprint(subject_basis)
    scenario_id = stable_identifier("CSC", fingerprint)
    subject_id = stable_identifier("CSUB", fingerprint)

    return LiveCertificationScenario(
        scenario_id=scenario_id,
        kind=kind,
        title=title,
        expected_status=expected_status,
        expected_article_id=expected_article_id,
        subject_id=subject_id,
        subject_title=f"C4.1 certification: {title}",
        subject_content=subject_content,
        subject_domain=subject_domain,
        source_article_fingerprint=source_article_fingerprint,
        fingerprint=fingerprint,
    )


def build_live_certification_scenarios(
    articles: Iterable[ArticleReference],
) -> tuple[LiveCertificationScenario, ...]:
    article = select_certification_article(articles)

    scenarios = (
        _scenario(
            kind=ScenarioKind.POSITIVE_COMPLIANCE.value,
            title="Live positive compliance",
            expected_status="compliant",
            article=article,
            subject_content=article.canonical_text,
            subject_domain=article.domain,
        ),
        _scenario(
            kind=ScenarioKind.NEGATIVE_COMPLIANCE.value,
            title="Live negative compliance",
            expected_status="noncompliant",
            article=article,
            subject_content=invert_normative_polarity(article.canonical_text),
            subject_domain=article.domain,
        ),
        _scenario(
            kind=ScenarioKind.REVIEW_REQUIRED.value,
            title="Live review required",
            expected_status="review_required",
            article=article,
            subject_content=build_review_content(article.canonical_text),
            subject_domain=article.domain,
        ),
        _scenario(
            kind=ScenarioKind.NOT_APPLICABLE.value,
            title="Live not applicable",
            expected_status="not_applicable",
            article=None,
            subject_content="quartz zephyr nebula xylophone",
            subject_domain="__constitutional_certification_unrelated__",
        ),
    )

    return tuple(sorted(scenarios, key=lambda item: item.scenario_id))
