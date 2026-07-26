from dataclasses import fields,is_dataclass
from datetime import datetime,timezone
from decimal import Decimal
from enum import Enum
from hashlib import sha256
import json
from pathlib import Path
from types import MappingProxyType
from typing import Any,Mapping
from .errors import ObservationSerializationError
def normalize_datetime(value):
    if not isinstance(value,datetime): raise ObservationSerializationError("datetime required")
    if value.tzinfo is None or value.utcoffset() is None: raise ObservationSerializationError("timezone-aware datetime required")
    return value.astimezone(timezone.utc).replace(microsecond=0)
def to_canonical_data(value):
    if isinstance(value,Enum): return value.value
    if isinstance(value,datetime): return normalize_datetime(value).isoformat()
    if isinstance(value,Decimal): return format(value,"f")
    if isinstance(value,Path): return str(value)
    if is_dataclass(value): return {f.name:to_canonical_data(getattr(value,f.name)) for f in fields(value)}
    if isinstance(value,(Mapping,MappingProxyType)): return {str(k):to_canonical_data(v) for k,v in sorted(value.items(),key=lambda p:str(p[0]))}
    if isinstance(value,(tuple,list)): return [to_canonical_data(v) for v in value]
    if isinstance(value,(set,frozenset)): return sorted((to_canonical_data(v) for v in value),key=lambda v:json.dumps(v,sort_keys=True,separators=(",",":")))
    if value is None or isinstance(value,(str,int,float,bool)): return value
    raise ObservationSerializationError(f"unsupported canonical value: {type(value).__name__}")
def canonical_json(value): return json.dumps(to_canonical_data(value),sort_keys=True,separators=(",",":"),ensure_ascii=False,allow_nan=False)
def canonical_fingerprint(value): return sha256(canonical_json(value).encode()).hexdigest()
def freeze_mapping(value): 
    data=dict(value or {}); to_canonical_data(data)
    return MappingProxyType(dict(sorted(data.items(),key=lambda p:str(p[0]))))
