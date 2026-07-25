from dataclasses import dataclass
from typing import Protocol
class IntegrationProjectionProvider(Protocol):
    def integration_health(self): ...
    def knowledge_readiness(self, query: str): ...
    def mission_control(self): ...
@dataclass(frozen=True, slots=True)
class ExecutiveApiEnvelope:
    status: str; source: str; timestamp: str; freshness: str; confidence: float; degraded_dependencies: tuple[str,...]; payload: object
def build_api_envelope(*,source,timestamp,payload,status='ok',freshness='current',confidence=1.0,degraded_dependencies=()):
    return ExecutiveApiEnvelope(status,source,timestamp,freshness,confidence,tuple(degraded_dependencies),payload)
