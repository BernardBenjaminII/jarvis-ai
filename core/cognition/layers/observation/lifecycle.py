from __future__ import annotations

from dataclasses import replace

from .enums import ObservationLifecycleState
from .errors import InvalidLifecycleTransitionError
from .models import ObservationRecord


class ObservationLifecycleManager:
    _allowed = {
        ObservationLifecycleState.DRAFT: {
            ObservationLifecycleState.VALIDATED,
            ObservationLifecycleState.REJECTED,
        },
        ObservationLifecycleState.VALIDATED: {
            ObservationLifecycleState.ACTIVE,
            ObservationLifecycleState.REJECTED,
        },
        ObservationLifecycleState.ACTIVE: {
            ObservationLifecycleState.SUPERSEDED,
            ObservationLifecycleState.RETIRED,
        },
        ObservationLifecycleState.SUPERSEDED: {
            ObservationLifecycleState.RETIRED,
        },
        ObservationLifecycleState.RETIRED: set(),
        ObservationLifecycleState.REJECTED: set(),
    }

    def transition(
        self,
        observation: ObservationRecord,
        target: ObservationLifecycleState,
    ) -> ObservationRecord:
        if target == observation.lifecycle_state:
            return observation

        permitted = self._allowed[observation.lifecycle_state]
        if target not in permitted:
            raise InvalidLifecycleTransitionError(
                f"Cannot transition {observation.lifecycle_state.value} "
                f"to {target.value}."
            )

        return replace(observation, lifecycle_state=target)


__all__ = ("ObservationLifecycleManager",)
