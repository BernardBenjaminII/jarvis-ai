from __future__ import annotations

from abc import ABC
from abc import abstractmethod
from typing import Any


class AssimilationHandler(ABC):
    """
    Canonical assimilation handler interface.

    Every knowledge-object handler must implement the same lifecycle.

    The Director orchestrates this lifecycle without knowledge of the
    concrete object type.
    """

    object_type: str

    # ------------------------------------------------------------------
    # Phase 1
    # ------------------------------------------------------------------

    @abstractmethod
    def plan(
        self,
        *,
        object_uuid: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Inspect the object and prepare an execution plan.

        Must not modify persistent state.
        """

    # ------------------------------------------------------------------
    # Phase 2
    # ------------------------------------------------------------------

    @abstractmethod
    def verify(
        self,
        *,
        object_uuid: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Verify prerequisites before execution.

        Examples:

            source exists

            permissions

            catalog state

            runtime availability
        """

    # ------------------------------------------------------------------
    # Phase 3
    # ------------------------------------------------------------------

    @abstractmethod
    def execute(
        self,
        *,
        object_uuid: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Execute assimilation.
        """

    # ------------------------------------------------------------------
    # Phase 4
    # ------------------------------------------------------------------

    @abstractmethod
    def recover(
        self,
        *,
        object_uuid: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Recover interrupted work.

        Default implementations may simply report that no recovery
        operation is required.
        """

    # ------------------------------------------------------------------
    # Phase 5
    # ------------------------------------------------------------------

    @abstractmethod
    def report(
        self,
        *,
        object_uuid: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Produce a structured execution report.
        """
