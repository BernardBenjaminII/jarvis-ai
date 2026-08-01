from __future__ import annotations

import hashlib
import json

from .contracts import ComplianceStatus, FindingSeverity
from .models import ArticleReference, ChangeSubject, ComplianceFinding, CompliancePolicy
from .normalize import excerpt, jaccard, polarity


def _hash(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
    ).hexdigest()


def evaluate_pair(
    subject: ChangeSubject,
    article: ArticleReference,
    policy: CompliancePolicy,
) -> ComplianceFinding | None:
    same_domain = subject.domain == article.domain
    score = jaccard(subject.content, article.canonical_text)

    if not same_domain and score < policy.minimum_match_score:
        return None
    if score < policy.minimum_match_score:
        return None

    contradictory = (
        score >= policy.contradiction_threshold
        and polarity(subject.content) != polarity(article.canonical_text)
    )

    if contradictory:
        status = ComplianceStatus.NONCOMPLIANT.value
        severity = FindingSeverity.ERROR.value
        rationale = "Subject has high lexical overlap with the article but opposite normative polarity."
    elif article.status == "review_required" and policy.fail_on_unresolved_article:
        status = ComplianceStatus.REVIEW_REQUIRED.value
        severity = FindingSeverity.WARNING.value
        rationale = "Applicable constitutional article remains unresolved and policy requires review."
    elif score >= policy.contradiction_threshold:
        status = ComplianceStatus.COMPLIANT.value
        severity = FindingSeverity.INFO.value
        rationale = "Subject materially aligns with the applicable constitutional article."
    else:
        status = ComplianceStatus.REVIEW_REQUIRED.value
        severity = FindingSeverity.WARNING.value
        rationale = "Subject appears constitutionally relevant but requires human interpretation."

    basis = {
        "subject_id": subject.subject_id,
        "article_id": article.article_id,
        "status": status,
        "severity": severity,
        "score": round(score, 6),
        "rationale": rationale,
    }
    fingerprint = _hash(basis)
    finding_id = "CF-" + fingerprint[:20].upper()

    return ComplianceFinding(
        finding_id=finding_id,
        subject_id=subject.subject_id,
        article_id=article.article_id,
        status=status,
        severity=severity,
        score=round(score, 6),
        rationale=rationale,
        subject_excerpt=excerpt(subject.content),
        article_excerpt=excerpt(article.canonical_text),
        fingerprint=fingerprint,
    )
