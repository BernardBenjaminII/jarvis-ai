from __future__ import annotations

from knowledge_engine.promotion.duplicate_detector import DuplicateDetector
from knowledge_engine.promotion.models import PromotionPlanItem
from knowledge_engine.promotion.organizer import destination_for


class PromotionPlanner:
    def __init__(self, db):
        self.db = db
        self.duplicates = DuplicateDetector(db)

    def plan(
        self,
        *,
        staging_root: str,
        knowledge_root: str,
        limit: int | None = None,
    ) -> list[PromotionPlanItem]:
        sql = """
            SELECT
                lc.object_uuid,
                lc.display_title,
                lc.subject,
                lc.object_type,
                lc.object_path,
                lc.quality_score
            FROM librarian_catalog lc
            WHERE lc.object_path LIKE ?
            ORDER BY lc.quality_score DESC, lc.display_title
        """
        params: list[object] = [f"%{staging_root}%"]

        if limit:
            sql += " LIMIT ?"
            params.append(limit)

        with self.db.connect() as conn:
            rows = conn.execute(sql, params).fetchall()

        items: list[PromotionPlanItem] = []

        for row in rows:
            title = row["display_title"] or row["object_path"]
            subject = row["subject"]
            object_type = row["object_type"]
            source_path = row["object_path"]

            destination = destination_for(
                knowledge_root=knowledge_root,
                title=title,
                subject=subject,
                object_type=object_type,
                source_path=source_path,
            )

            duplicate_state, duplicate_reason = self.duplicates.classify_duplicate_risk(
                object_uuid=row["object_uuid"],
                title=title,
                subject=subject,
                object_type=object_type,
                destination_path=destination,
            )

            quality = float(row["quality_score"] or 0)

            if quality < 0.4:
                action = "skip"
                reason = "quality score below promotion threshold"
            elif duplicate_state == "duplicate_destination":
                action = "skip"
                reason = duplicate_reason
            elif duplicate_state == "possible_duplicate":
                action = "review"
                reason = duplicate_reason
            else:
                action = "promote"
                reason = "cataloged, enriched, unique, and eligible for promotion"

            items.append(
                PromotionPlanItem(
                    object_uuid=row["object_uuid"],
                    title=title,
                    subject=subject,
                    object_type=object_type,
                    source_path=source_path,
                    destination_path=destination,
                    action=action,
                    reason=reason,
                )
            )

        return items
