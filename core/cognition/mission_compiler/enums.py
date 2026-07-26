from __future__ import annotations

from enum import Enum


class MissionPlanStatus(str, Enum):
    COMPILED = "compiled"
    INVALID = "invalid"


class MissionPriority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class NodeKind(str, Enum):
    OBJECTIVE = "objective"
    TASK = "task"
    ACTIVITY = "activity"


class ActivityExecutionMode(str, Enum):
    HUMAN = "human"
    AUTOMATED = "automated"
    HYBRID = "hybrid"
