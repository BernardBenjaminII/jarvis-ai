from dataclasses import dataclass
@dataclass(frozen=True,slots=True)
class FailedCandidate:
 candidate_id:str; path:str; title:str; category:str|None; extension:str; sha256:str|None; detail:str; attempts:int
@dataclass(frozen=True,slots=True)
class ExtractionOutcome:
 candidate_id:str; path:str; strategy:str; status:str; text:str; detail:str; chars:int; pages:int|None=None
