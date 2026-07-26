from dataclasses import fields,is_dataclass
from enum import Enum
from typing import Mapping
def to_canonical_data(v):
    if isinstance(v,Enum): return v.value
    if is_dataclass(v): return {f.name:to_canonical_data(getattr(v,f.name)) for f in fields(v)}
    if isinstance(v,Mapping): return {str(k):to_canonical_data(x) for k,x in sorted(v.items(),key=lambda p:str(p[0]))}
    if isinstance(v,(tuple,list)): return [to_canonical_data(x) for x in v]
    return v
