from __future__ import annotations


def catalog_quality_score(
    title: str | None,
    subject: str | None,
    resource_type: str | None,
    keywords: str | None,
    metadata_json: str | None,
) -> float:
    score = 0.0

    if title:
        score += 0.25
    if subject:
        score += 0.25
    if resource_type:
        score += 0.15
    if keywords:
        score += 0.15
    if metadata_json and metadata_json not in {"{}", "null"}:
        score += 0.20

    return round(min(score, 1.0), 2)
