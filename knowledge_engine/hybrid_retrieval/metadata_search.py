from __future__ import annotations

import re


def tokenize(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9_+-]+", text.lower()))


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
                    lc.object_uuid,
                    lc.object_path,
                    lc.object_type,
                    lc.canonical_title,
                    lc.display_title,
                    lc.subject,
                    lc.keywords,
                    lc.description,
                    lc.quality_score,
                    lc.subject_confidence,
                    COALESCE(ce.aliases, '') AS aliases,
                    COALESCE(ce.search_terms, '') AS search_terms,
                    COALESCE(ce.entities, '') AS entities,
                    COALESCE(ce.topics, '') AS topics
                FROM librarian_catalog lc
                LEFT JOIN catalog_enrichment ce
                  ON ce.object_uuid = lc.object_uuid
                """
            ).fetchall()

        for row in rows:
            title = f"{row['canonical_title'] or ''} {row['display_title'] or ''}".lower()
            subject = str(row["subject"] or "").lower()
            keywords = str(row["keywords"] or "").lower()
            description = str(row["description"] or "").lower()
            object_type = str(row["object_type"] or "").lower()
            path = str(row["object_path"] or "").lower()
            aliases = str(row["aliases"] or "").lower()
            search_terms = str(row["search_terms"] or "").lower()
            entities = str(row["entities"] or "").lower()
            topics = str(row["topics"] or "").lower()

            haystack = " ".join(
                [
                    title,
                    subject,
                    keywords,
                    description,
                    object_type,
                    path,
                    aliases,
                    search_terms,
                    entities,
                    topics,
                ]
            )

            h_tokens = tokenize(haystack)
            overlap = len(q_tokens & h_tokens)

            if overlap == 0:
                continue

            score = 0.0

            # Generic overlap.
            score += overlap * 0.12

            # Strong fields.
            score += sum(0.35 for token in q_tokens if token in title)
            score += sum(0.30 for token in q_tokens if token in aliases)
            score += sum(0.30 for token in q_tokens if token in entities)
            score += sum(0.25 for token in q_tokens if token in topics)
            score += sum(0.22 for token in q_tokens if token in subject)
            score += sum(0.18 for token in q_tokens if token in keywords)
            score += sum(0.12 for token in q_tokens if token in search_terms)
            score += sum(0.08 for token in q_tokens if token in path)

            score += float(row["quality_score"] or 0) * 0.10
            score += float(row["subject_confidence"] or 0) * 0.05

            scores[row["object_uuid"]] = min(score, 2.0)

        return scores
