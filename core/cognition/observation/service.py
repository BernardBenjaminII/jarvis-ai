from __future__ import annotations
from .models import Observation, ObservationProvenance
from .enums import ObservationKind, ObservationSeverity, SourceAuthority

class ExecutiveObservationService:
    def __init__(self,bus): self.bus=bus
    def record(self, *, observation_type, kind, value, producer, source, occurred_at,
               authority=SourceAuthority.UNKNOWN, source_reference=None, provenance_attributes=None,
               confidence=1.0, severity=ObservationSeverity.INFORMATIONAL, mission_id=None,
               correlation_id=None, causation_id=None, labels=None, observation_id=None):
        provenance=ObservationProvenance.create(producer=producer,source=source,authority=authority,
                                                source_reference=source_reference,attributes=provenance_attributes)
        observation=Observation.create(observation_type=observation_type,kind=kind,value=value,
                                       provenance=provenance,occurred_at=occurred_at,confidence=confidence,
                                       severity=severity,mission_id=mission_id,correlation_id=correlation_id,
                                       causation_id=causation_id,labels=labels,observation_id=observation_id)
        return self.bus.publish(observation)
