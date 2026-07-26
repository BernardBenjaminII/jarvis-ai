from enum import Enum

class CapabilityLifecycle(str, Enum):
    PLANNED='planned'; IMPLEMENTED='implemented'; CONFIGURED='configured'; AVAILABLE='available'; DEGRADED='degraded'; UNAVAILABLE='unavailable'; NOT_CONNECTED='not_connected'
class HealthStatus(str, Enum):
    HEALTHY='healthy'; DEGRADED='degraded'; UNAVAILABLE='unavailable'; UNKNOWN='unknown'
class IntegrationStatus(str, Enum):
    CONNECTED='connected'; DEGRADED='degraded'; NOT_CONNECTED='not_connected'; UNAVAILABLE='unavailable'; UNKNOWN='unknown'
class VisibilitySurface(str, Enum):
    RUNTIME='runtime'; API='api'; UI='ui'; TELEMETRY='telemetry'; KNOWLEDGE='knowledge'
class KnowledgeCoverageStatus(str, Enum):
    SUFFICIENT='sufficient'; PARTIAL='partial'; INSUFFICIENT='insufficient'; UNKNOWN='unknown'
class Severity(str, Enum):
    INFO='info'; WARNING='warning'; CRITICAL='critical'
