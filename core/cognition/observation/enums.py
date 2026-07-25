from __future__ import annotations
from enum import Enum

class ObservationKind(str, Enum):
    ACTIVITY="activity"; EVENT="event"; HEALTH="health"; KNOWLEDGE="knowledge"
    METRIC="metric"; SECURITY="security"; STATE="state"; TELEMETRY="telemetry"

class ObservationSeverity(str, Enum):
    DEBUG="debug"; INFORMATIONAL="informational"; NOTICE="notice"
    WARNING="warning"; ERROR="error"; CRITICAL="critical"

class SourceAuthority(str, Enum):
    UNKNOWN="unknown"; USER="user"; INFERRED="inferred"; EXTERNAL="external"
    SYSTEM="system"; CONSTITUTIONAL="constitutional"

class ObservationDisposition(str, Enum):
    ACCEPTED="accepted"; DUPLICATE="duplicate"; REJECTED="rejected"
