from datetime import datetime,timezone
from enum import Enum
from .contracts import Observation,ObservationContext,ObservationSource,utc_now
from .enums import *
from .errors import ObservationAdapterError
def _v(x): return x.value if isinstance(x,Enum) else x
def _dt(x):
    x=x or utc_now()
    if not isinstance(x,datetime): raise ObservationAdapterError("legacy timestamp must be datetime")
    return x if x.tzinfo else x.replace(tzinfo=timezone.utc)
def _kind(x):
    raw=str(_v(x) or "custom").lower()
    return next((k for k in ObservationKind if k.value==raw),ObservationKind.CUSTOM)
def _severity(x):
    raw=str(_v(x) or "none").lower()
    return next((k for k in ObservationSeverity if k.value==raw),ObservationSeverity.NONE)
def _domain(t,k):
    p=t.split(".",1)[0].lower()
    return next((d for d in ObservationDomain if d.value==p),ObservationDomain.KNOWLEDGE if k in {ObservationKind.KNOWLEDGE,ObservationKind.DOCUMENT,ObservationKind.CONTENT} else ObservationDomain.CUSTOM)
def adapt_executive_observation(legacy):
    t=str(getattr(legacy,"observation_type","legacy.observation")); k=_kind(getattr(legacy,"kind",None)); p=getattr(legacy,"provenance",None)
    source=ObservationSource.create(reality_class=RealityClass.RECORDED if k in {ObservationKind.KNOWLEDGE,ObservationKind.DOCUMENT,ObservationKind.CONTENT} else RealityClass.LIVE,source_type=SourceType.KNOWLEDGE_DOCUMENT if k in {ObservationKind.KNOWLEDGE,ObservationKind.DOCUMENT,ObservationKind.CONTENT} else SourceType.EXECUTIVE_SUBSYSTEM,identifier=str(getattr(p,"source",getattr(p,"source_id","unknown"))),producer=str(getattr(p,"producer","legacy")),authority=next((a for a in SourceAuthority if a.value==str(_v(getattr(p,"authority","unknown"))).lower()),SourceAuthority.UNKNOWN))
    return Observation.create(domain=_domain(t,k),observation_type=t,kind=k,subject=str(getattr(legacy,"subject",t)),predicate=str(getattr(legacy,"predicate","reports")),value=getattr(legacy,"value",None),source=source,observed_at=_dt(getattr(legacy,"occurred_at",getattr(legacy,"observed_at",None))),recorded_at=_dt(getattr(legacy,"recorded_at",None)),confidence=float(getattr(legacy,"confidence",1.0)),severity=_severity(getattr(legacy,"severity",None)),context=ObservationContext(mission_id=str(getattr(legacy,"mission_id","") or "")),metadata={"legacy_contract":type(legacy).__qualname__,"legacy_observation_id":str(getattr(legacy,"observation_id",""))})
def adapt_cognition_observation(legacy):
    r=getattr(legacy,"source",None); vo=getattr(legacy,"value",None); raw=getattr(vo,"value",vo); pred=str(getattr(legacy,"predicate","reports"))
    source=ObservationSource.create(reality_class=RealityClass.RECORDED,source_type=SourceType.KNOWLEDGE_DOCUMENT,identifier=str(getattr(r,"source_id","unknown")),segment_id=str(getattr(r,"segment_id","") or ""),start_offset=getattr(r,"start_offset",None),end_offset=getattr(r,"end_offset",None),excerpt=str(getattr(r,"excerpt","") or ""))
    return Observation.create(domain=ObservationDomain.KNOWLEDGE,observation_type=f"knowledge.{pred}",kind=ObservationKind.CONTENT,subject=str(getattr(legacy,"subject","unknown")),predicate=pred,value=raw,source=source,observed_at=_dt(getattr(legacy,"observed_at",getattr(legacy,"created_at",None))),confidence=float(getattr(legacy,"confidence",1.0)),unit=str(getattr(vo,"unit","") or ""),metadata={"legacy_contract":type(legacy).__qualname__,"legacy_observation_id":str(getattr(legacy,"observation_id",""))})
def adapt_legacy_observation(legacy):
    if isinstance(legacy,Observation): return legacy
    if hasattr(legacy,"provenance") and hasattr(legacy,"observation_type"): return adapt_executive_observation(legacy)
    if all(hasattr(legacy,n) for n in ("subject","predicate","source")): return adapt_cognition_observation(legacy)
    raise ObservationAdapterError(f"unsupported legacy observation shape: {type(legacy).__module__}.{type(legacy).__qualname__}")
