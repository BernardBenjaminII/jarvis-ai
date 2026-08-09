from dataclasses import dataclass, field
from typing import Any

@dataclass(frozen=True, slots=True)
class CandidateForensicRecord:
    candidate_id:str
    title:str
    source_path:str
    raw_rank:int
    retrieval_score:float|None
    lexical_score:float|None
    phrase_score:float|None
    subject_score:float|None
    confidence_score:float|None
    final_score:float|None
    threshold:float|None
    margin:float|None
    decision:str
    rejection_reason:str|None
    explanation:str
    metadata:dict[str,Any]=field(default_factory=dict)
    def to_dict(self):
        return {
            "candidate_id":self.candidate_id,"title":self.title,"source_path":self.source_path,
            "raw_rank":self.raw_rank,"retrieval_score":self.retrieval_score,
            "lexical_score":self.lexical_score,"phrase_score":self.phrase_score,
            "subject_score":self.subject_score,"confidence_score":self.confidence_score,
            "final_score":self.final_score,"threshold":self.threshold,"margin":self.margin,
            "decision":self.decision,"rejection_reason":self.rejection_reason,
            "explanation":self.explanation,"metadata":dict(self.metadata),
        }

@dataclass(frozen=True, slots=True)
class ProbeForensicResult:
    probe_id:str
    query:str
    expectation:str
    raw_count:int
    qualified_count:int
    raw_error:str|None
    qualified_error:str|None
    candidates:tuple[CandidateForensicRecord,...]
    dominant_failure:str|None
    recommendations:tuple[str,...]
    def to_dict(self):
        return {
            "probe_id":self.probe_id,"query":self.query,"expectation":self.expectation,
            "raw_count":self.raw_count,"qualified_count":self.qualified_count,
            "raw_error":self.raw_error,"qualified_error":self.qualified_error,
            "candidates":[x.to_dict() for x in self.candidates],
            "dominant_failure":self.dominant_failure,
            "recommendations":list(self.recommendations),
        }

@dataclass(frozen=True, slots=True)
class RuntimeForensicReport:
    status:str
    classification:str
    probes:tuple[ProbeForensicResult,...]
    summary:dict[str,Any]
    recommendations:tuple[str,...]
    def to_dict(self):
        return {
            "status":self.status,"classification":self.classification,
            "probes":[x.to_dict() for x in self.probes],
            "summary":dict(self.summary),
            "recommendations":list(self.recommendations),
        }
