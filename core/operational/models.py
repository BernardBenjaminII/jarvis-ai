from dataclasses import dataclass, field
from hashlib import sha256
import json
from typing import Mapping

@dataclass(frozen=True, slots=True)
class BootCheck:
    name:str; status:str; detail:str=''
    def to_dict(self): return {'name':self.name,'status':self.status,'detail':self.detail}

@dataclass(frozen=True, slots=True)
class OperationalSnapshot:
    cycle:int; state:str; government_fingerprint:str; object_count:int; relationship_count:int; readiness_percent:int; health:str; checks:tuple[BootCheck,...]=(); metrics:Mapping[str,str]=field(default_factory=dict)
    def to_dict(self):
        return {'cycle':self.cycle,'state':self.state,'government_fingerprint':self.government_fingerprint,'object_count':self.object_count,'relationship_count':self.relationship_count,'readiness_percent':self.readiness_percent,'health':self.health,'checks':[c.to_dict() for c in self.checks],'metrics':dict(sorted((str(k),str(v)) for k,v in self.metrics.items()))}
    @property
    def fingerprint(self): return sha256(json.dumps(self.to_dict(),sort_keys=True,separators=(',',':')).encode()).hexdigest()
