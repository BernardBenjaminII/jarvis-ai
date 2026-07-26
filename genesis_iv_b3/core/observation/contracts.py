from __future__ import annotations
from dataclasses import dataclass,field
from datetime import datetime,timezone
from types import MappingProxyType
from typing import Any,Mapping
from .enums import *
from .errors import ObservationValidationError
from .serialization import canonical_fingerprint,freeze_mapping,normalize_datetime,to_canonical_data
SCHEMA_VERSION="ocs-0000/1.0"
def utc_now(): return datetime.now(timezone.utc).replace(microsecond=0)
def _required(v,n):
    v=str(v).strip()
    if not v: raise ObservationValidationError(f"{n} is required")
    return v
@dataclass(frozen=True,slots=True)
class ObservationSource:
    reality_class: RealityClass
    source_type: SourceType
    identifier: str
    kind: str=""
    producer: str=""
    collector: str=""
    version: str=""
    authority: SourceAuthority=SourceAuthority.UNKNOWN
    uri: str=""
    content_fingerprint: str=""
    segment_id: str=""
    start_offset: int|None=None
    end_offset: int|None=None
    excerpt: str=""
    metadata: Mapping[str,Any]=field(default_factory=lambda:MappingProxyType({}))
    def __post_init__(self):
        object.__setattr__(self,"identifier",_required(self.identifier,"source.identifier"))
        for n in ("kind","producer","collector","version","uri","content_fingerprint","segment_id","excerpt"): object.__setattr__(self,n,str(getattr(self,n)).strip())
        if self.start_offset is not None and self.start_offset<0: raise ObservationValidationError("negative start_offset")
        if self.end_offset is not None and self.end_offset<0: raise ObservationValidationError("negative end_offset")
        if self.start_offset is not None and self.end_offset is not None and self.end_offset<self.start_offset: raise ObservationValidationError("end_offset precedes start_offset")
        object.__setattr__(self,"metadata",freeze_mapping(self.metadata))
    @classmethod
    def create(cls,*,reality_class,source_type,identifier,**kwargs): return cls(RealityClass(reality_class),SourceType(source_type),identifier,**kwargs)
@dataclass(frozen=True,slots=True)
class ObservationContext:
    mission_id:str=""; objective_id:str=""; task_id:str=""; activity_id:str=""; session_id:str=""; correlation_id:str=""; trace_id:str=""
    tags:tuple[str,...]=()
    metadata:Mapping[str,Any]=field(default_factory=lambda:MappingProxyType({}))
    def __post_init__(self):
        for n in ("mission_id","objective_id","task_id","activity_id","session_id","correlation_id","trace_id"): object.__setattr__(self,n,str(getattr(self,n)).strip())
        object.__setattr__(self,"tags",tuple(sorted({str(x).strip() for x in self.tags if str(x).strip()})))
        object.__setattr__(self,"metadata",freeze_mapping(self.metadata))
@dataclass(frozen=True,slots=True)
class Observation:
    observation_id:str
    domain:ObservationDomain
    observation_type:str
    kind:ObservationKind
    subject:str
    predicate:str
    value:Any
    source:ObservationSource
    observed_at:datetime
    recorded_at:datetime
    confidence:float
    severity:ObservationSeverity=ObservationSeverity.NONE
    priority:ObservationPriority=ObservationPriority.NORMAL
    status:ObservationStatus=ObservationStatus.ACTIVE
    context:ObservationContext=field(default_factory=ObservationContext)
    unit:str=""; statement:str=""; supersedes_observation_id:str|None=None
    schema_version:str=SCHEMA_VERSION
    metadata:Mapping[str,Any]=field(default_factory=lambda:MappingProxyType({}))
    def __post_init__(self):
        for n in ("observation_id","observation_type","subject","predicate"): object.__setattr__(self,n,_required(getattr(self,n),n))
        object.__setattr__(self,"observed_at",normalize_datetime(self.observed_at)); object.__setattr__(self,"recorded_at",normalize_datetime(self.recorded_at))
        if not 0<=float(self.confidence)<=1: raise ObservationValidationError("confidence must be between 0 and 1")
        object.__setattr__(self,"confidence",float(self.confidence)); to_canonical_data(self.value); object.__setattr__(self,"metadata",freeze_mapping(self.metadata))
        expected=self.compute_identity(domain=self.domain,observation_type=self.observation_type,kind=self.kind,subject=self.subject,predicate=self.predicate,value=self.value,source=self.source,observed_at=self.observed_at,unit=self.unit,statement=self.statement,supersedes_observation_id=self.supersedes_observation_id,schema_version=self.schema_version)
        if self.observation_id!=expected: raise ObservationValidationError("observation_id does not match canonical content")
    @staticmethod
    def compute_identity(**kwargs): return "obs-"+canonical_fingerprint(kwargs)[:32]
    @classmethod
    def create(cls,*,domain,observation_type,kind,subject,predicate,value,source,observed_at,recorded_at=None,confidence=1.0,severity=ObservationSeverity.NONE,priority=ObservationPriority.NORMAL,status=ObservationStatus.ACTIVE,context=None,unit="",statement="",supersedes_observation_id=None,schema_version=SCHEMA_VERSION,metadata=None):
        domain=ObservationDomain(domain); kind=ObservationKind(kind); observed_at=normalize_datetime(observed_at)
        identity=cls.compute_identity(domain=domain,observation_type=_required(observation_type,"observation_type"),kind=kind,subject=_required(subject,"subject"),predicate=_required(predicate,"predicate"),value=value,source=source,observed_at=observed_at,unit=str(unit).strip(),statement=str(statement).strip(),supersedes_observation_id=(str(supersedes_observation_id).strip() if supersedes_observation_id else None),schema_version=schema_version)
        return cls(identity,domain,observation_type,kind,subject,predicate,value,source,observed_at,recorded_at or utc_now(),confidence,ObservationSeverity(severity),ObservationPriority(priority),ObservationStatus(status),context or ObservationContext(),unit,statement,supersedes_observation_id,schema_version,metadata or {})
    @property
    def fingerprint(self): return canonical_fingerprint(self)
    def to_canonical_data(self): return to_canonical_data(self)
