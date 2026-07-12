from __future__ import annotations

from typing import Any

from knowledge_engine.assimilation.handlers.base import (
    AssimilationHandler,
)
from knowledge_engine.assimilation.runner import (
    AssimilationRunner,
)


class SingleDocumentHandler(AssimilationHandler):

    object_type = "single_document"

    def __init__(
        self,
        runner: AssimilationRunner,
    ):
        self.runner = runner

    def plan(
        self,
        *,
        object_uuid: str,
        **kwargs: Any,
    ) -> dict[str, Any]:

        return {
            "status": "planned",
            "object_uuid": object_uuid,
        }

    def verify(
        self,
        *,
        object_uuid: str,
        **kwargs: Any,
    ) -> dict[str, Any]:

        return {
            "status": "verified",
            "object_uuid": object_uuid,
        }

    def execute(
        self,
        *,
        object_uuid: str,
        **kwargs: Any,
    ) -> dict[str, Any]:

        return self.runner.run_one_single_document(
            expected_object_uuid=object_uuid,
        )

    def recover(
        self,
        *,
        object_uuid: str,
        **kwargs: Any,
    ) -> dict[str, Any]:

        return {
            "status": "no_recovery_required",
            "object_uuid": object_uuid,
        }

    def report(
        self,
        *,
        object_uuid: str,
        **kwargs: Any,
    ) -> dict[str, Any]:

        return {
            "status": "report_available",
            "object_uuid": object_uuid,
        }
