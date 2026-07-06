from __future__ import annotations

from knowledge_engine.promotion.models import PromotionPlanItem
from knowledge_engine.promotion.organizer import destination_for


class PromotionPlanner:
    def __init__(self, db):
        self.db = db

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
            source_path = row["object_path"]
            object_type = row["object_type"]
            subject = row["subject"]

            destination = destination_for(
                knowledge_root=knowledge_root,
                title=title,
                subject=subject,
                object_type=object_type,
                source_path=source_path,
            )

            if row["quality_score"] is not None and float(row["quality_score"]) < 0.4:
                action = "skip"
                reason = "quality score below promotion threshold"
            else:
                action = "promote"
                reason = "cataloged, enriched, and eligible for promotion"

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
