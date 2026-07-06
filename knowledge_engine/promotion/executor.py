from __future__ import annotations

import shutil
from pathlib import Path

from knowledge_engine.promotion.models import PromotionPlanItem
from knowledge_engine.promotion.store import init_promotion


class PromotionExecutor:
    def __init__(self, db):
        self.db = db

    def execute(self, items: list[PromotionPlanItem]) -> dict:
        promoted = 0
        skipped = 0
        errors: list[tuple[str, str]] = []

        with self.db.connect() as conn:
            init_promotion(conn)

            for item in items:
                if item.action != "promote":
                    skipped += 1
                    continue

                try:
                    src = Path(item.source_path)
                    dst = Path(item.destination_path)
                    dst.parent.mkdir(parents=True, exist_ok=True)

                    if dst.exists():
                        skipped += 1
                        reason = "destination already exists"
                    else:
                        if src.is_dir():
                            shutil.copytree(src, dst)
                        else:
                            shutil.copy2(src, dst)

                        promoted += 1
                        reason = item.reason

                    conn.execute(
                        """
                        INSERT INTO promotion_history (
                            object_uuid, action, source_path, destination_path, reason
                        )
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (
                            item.object_uuid,
                            item.action,
                            item.source_path,
                            item.destination_path,
                            reason,
                        ),
                    )

                except Exception as exc:
                    errors.append((item.source_path, str(exc)))

            conn.commit()

        return {
            "promoted": promoted,
            "skipped": skipped,
            "promotion_errors": errors,
        }
