from dataclasses import dataclass
from typing import Any
@dataclass(frozen=True,slots=True)
class CensusReport:
 status:str; classification:str; databases:tuple[dict[str,Any],...]; executive_compatibility:dict[str,Any]; recommendations:tuple[str,...]; summary:dict[str,Any]
 def to_dict(self): return {"status":self.status,"classification":self.classification,"databases":[dict(x) for x in self.databases],"executive_compatibility":dict(self.executive_compatibility),"recommendations":list(self.recommendations),"summary":dict(self.summary)}
