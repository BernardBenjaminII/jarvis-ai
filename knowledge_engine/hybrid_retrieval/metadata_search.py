from __future__ import annotations

import re


def tokenize(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9_]+", text.lower()))


class MetadataSearcher:
    def __init__(self, db):
        self.db = db

    def score_resources(self, query: str) -> dict[str, float]:
        q_tokens = tokenize(query)

        if not q_tokens:
            return {}

        scores: dict[str, float] = {}

        with self.db.connect() as conn:
            rows = conn.execute(
                """
                SELECT
                    object_uuid,
                    object_path,
                    object_type,
                    canonical_title,
                    display_title,
                    subject,
                    keywords,
                    description,
                    quality_score,
                    subject_confidence
                FROM librarian_catalog
                """
            ).fetchall()

        for row in rows:
            haystack = " ".join(
                str(row[key] or "")
                for key in [
                    "object_path",
                    "object_type",
                    "canonical_title",
                    "display_title",
                    "subject",
                    "keywords",
                    "description",
                ]
            ).lower()

            h_tokens = tokenize(haystack)
            overlap = len(q_tokens & h_tokens)

            if overlap == 0:
                continue

            score = 0.0
            score += overlap * 0.20

            title = f"{row['canonical_title'] or ''} {row['display_title'] or ''}".lower()
            subject = str(row["subject"] or "").lower()
            keywords = str(row["keywords"] or "").lower()

            if any(token in title for token in q_tokens):
                score += 0.40

            if any(token in subject for token in q_tokens):
                score += 0.30

            if any(token in keywords for token in q_tokens):
                score += 0.25

            score += float(row["quality_score"] or 0) * 0.20
            score += float(row["subject_confidence"] or 0) * 0.10

            scores[row["object_uuid"]] = min(score, 1.0)

        return scores
