from __future__ import annotations

from collections import defaultdict

from .fingerprints import canonical_fingerprint
from .models import ArticleUsage


def build_article_usage(
    *,
    article_ids: tuple[str, ...],
    findings: tuple[dict, ...],
) -> tuple[ArticleUsage, ...]:
    usage: dict[str, list[dict]] = defaultdict(list)
    for finding in findings:
        usage[str(finding["article_id"])].append(finding)

    results = []
    for article_id in sorted(article_ids):
        article_findings = usage.get(article_id, [])
        artifact_ids = tuple(
            sorted({str(item["subject_id"]) for item in article_findings})
        )
        counts = defaultdict(int)
        for item in article_findings:
            counts[str(item["status"])] += 1

        basis = {
            "article_id": article_id,
            "reference_count": len(article_findings),
            "compliant_count": counts["compliant"],
            "review_required_count": counts["review_required"],
            "noncompliant_count": counts["noncompliant"],
            "artifact_ids": list(artifact_ids),
        }
        results.append(
            ArticleUsage(
                article_id=article_id,
                reference_count=basis["reference_count"],
                compliant_count=basis["compliant_count"],
                review_required_count=basis["review_required_count"],
                noncompliant_count=basis["noncompliant_count"],
                artifact_ids=artifact_ids,
                usage_fingerprint=canonical_fingerprint(basis),
            )
        )

    return tuple(results)
