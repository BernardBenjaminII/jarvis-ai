from __future__ import annotations
import hashlib, json, math
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping
from .enums import ObservationDisposition, ObservationKind, ObservationSeverity, SourceAuthority
from .errors import InvalidObservationError

def _dt(v: datetime, name: str) -> datetime:
    if not isinstance(v, datetime) or v.tzinfo is None or v.utcoffset() is None:
        raise InvalidObservationError(f"{name} must be timezone-aware")
    return v.astimezone(timezone.utc)

def _conf(v: float) -> float:
    v=float(v)
    if not math.isfinite(v) or not 0.0 <= v <= 1.0:
        raise InvalidObservationError("confidence must be between 0.0 and 1.0")
    return v

def _json(v: Any, path: str="value") -> Any:
    if v is None or isinstance(v,(str,int,bool)): return v
    if isinstance(v,float):
        if not math.isfinite(v): raise InvalidObservationError(f"{path} contains non-finite number")
        return v
    if isinstance(v,datetime): return _dt(v,path).isoformat()
    if isinstance(v,Mapping):
        out={}
        for k,x in v.items():
            k=str(k).strip()
            if not k: raise InvalidObservationError(f"{path} contains empty key")
            out[k]=_json(x,f"{path}.{k}")
        return {k:out[k] for k in sorted(out)}
    if isinstance(v,(list,tuple)): return [_json(x,f"{path}[]") for x in v]
    raise InvalidObservationError(f"{path} contains unsupported type {type(v).__name__}")

def _pairs(m: Mapping[str, Any] | None) -> tuple[tuple[str, Any], ...]:
    if not m: return ()
    out=[]
    for k,v in m.items():
        k=str(k).strip()
        if not k: raise InvalidObservationError("mapping keys must not be empty")
        out.append((k,_json(v,k)))
    return tuple(sorted(out))

def _canon(v: Mapping[str,Any]) -> str:
    return json.dumps(v,sort_keys=True,separators=(",",":"),ensure_ascii=True,allow_nan=False)

@dataclass(frozen=True, slots=True)
class ObservationProvenance:
    producer: str
    source: str
    authority: SourceAuthority=SourceAuthority.UNKNOWN
    source_reference: str|None=None
    attributes: tuple[tuple[str,Any],...]=()
    def __post_init__(self):
        for n in ("producer","source"):
            x=str(getattr(self,n)).strip()
            if not x: raise InvalidObservationError(f"{n} must not be empty")
            object.__setattr__(self,n,x)
        if not isinstance(self.authority,SourceAuthority):
            object.__setattr__(self,"authority",SourceAuthority(str(self.authority)))
        object.__setattr__(self,"attributes",_pairs(dict(self.attributes)))
    @classmethod
    def create(cls, *, producer:str, source:str, authority:SourceAuthority=SourceAuthority.UNKNOWN,
               source_reference:str|None=None, attributes:Mapping[str,Any]|None=None):
        return cls(producer,source,authority,source_reference,_pairs(attributes))
    def to_canonical_dict(self):
        return {"producer":self.producer,"source":self.source,"authority":self.authority.value,
                "source_reference":self.source_reference,"attributes":dict(self.attributes)}

@dataclass(frozen=True, slots=True)
class Observation:
    observation_id: str
    observation_type: str
    kind: ObservationKind
    value: Any
    provenance: ObservationProvenance
    occurred_at: datetime
    recorded_at: datetime
    confidence: float=1.0
    severity: ObservationSeverity=ObservationSeverity.INFORMATIONAL
    mission_id: str|None=None
    correlation_id: str|None=None
    causation_id: str|None=None
    labels: tuple[tuple[str,str],...]=()
    @classmethod
    def create(cls, *, observation_type:str, kind:ObservationKind, value:Any,
               provenance:ObservationProvenance, occurred_at:datetime, recorded_at:datetime|None=None,
               confidence:float=1.0, severity:ObservationSeverity=ObservationSeverity.INFORMATIONAL,
               mission_id:str|None=None, correlation_id:str|None=None, causation_id:str|None=None,
               labels:Mapping[str,str]|None=None, observation_id:str|None=None):
        observation_type=str(observation_type).strip()
        if not observation_type: raise InvalidObservationError("observation_type must not be empty")
        kind = kind if isinstance(kind,ObservationKind) else ObservationKind(str(kind))
        severity = severity if isinstance(severity,ObservationSeverity) else ObservationSeverity(str(severity))
        occurred_at=_dt(occurred_at,"occurred_at"); confidence=_conf(confidence); value=_json(value)
        label_pairs=tuple((str(k).strip(),str(v).strip()) for k,v in sorted((labels or {}).items()))
        payload={"observation_type":observation_type,"kind":kind.value,"value":value,
                 "provenance":provenance.to_canonical_dict(),"occurred_at":occurred_at.isoformat(),
                 "confidence":confidence,"severity":severity.value,"mission_id":mission_id,
                 "correlation_id":correlation_id,"causation_id":causation_id,"labels":dict(label_pairs)}
        oid=observation_id or "obs_"+hashlib.sha256(_canon(payload).encode()).hexdigest()
        return cls(oid,observation_type,kind,value,provenance,occurred_at,_dt(recorded_at or datetime.now(timezone.utc),"recorded_at"),
                   confidence,severity,mission_id,correlation_id,causation_id,label_pairs)
    def to_canonical_dict(self):
        return {"observation_id":self.observation_id,"observation_type":self.observation_type,
                "kind":self.kind.value,"value":self.value,"provenance":self.provenance.to_canonical_dict(),
                "occurred_at":self.occurred_at.isoformat(),"recorded_at":self.recorded_at.isoformat(),
                "confidence":self.confidence,"severity":self.severity.value,"mission_id":self.mission_id,
                "correlation_id":self.correlation_id,"causation_id":self.causation_id,"labels":dict(self.labels)}
    def fingerprint(self): return hashlib.sha256(_canon(self.to_canonical_dict()).encode()).hexdigest()

@dataclass(frozen=True, slots=True)
class ObservationQuery:
    observation_type:str|None=None; kind:ObservationKind|None=None; producer:str|None=None
    source:str|None=None; mission_id:str|None=None; correlation_id:str|None=None
    minimum_confidence:float|None=None; minimum_severity:ObservationSeverity|None=None
    occurred_from:datetime|None=None; occurred_to:datetime|None=None; limit:int|None=None
    newest_first:bool=False

@dataclass(frozen=True, slots=True)
class PublicationReceipt:
    observation_id:str
    disposition:ObservationDisposition
    subscriber_count:int
    subscriber_failures:tuple[str,...]=()
    @property
    def accepted(self): return self.disposition is ObservationDisposition.ACCEPTED
    @property
    def duplicate(self): return self.disposition is ObservationDisposition.DUPLICATE
