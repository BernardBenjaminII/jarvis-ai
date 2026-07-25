from dataclasses import fields, is_dataclass
from enum import Enum
from typing import Mapping

def to_canonical_data(value):
    if isinstance(value,Enum): return value.value
    if is_dataclass(value): return {f.name:to_canonical_data(getattr(value,f.name)) for f in fields(value)}
    if isinstance(value,Mapping): return {str(k):to_canonical_data(v) for k,v in sorted(value.items(),key=lambda p:str(p[0]))}
    if isinstance(value,(tuple,list)): return [to_canonical_data(v) for v in value]
    return value
