from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Mapping, Tuple
from .enums import AuthorityStatus, CandidateDisposition, ConstitutionalStatus, DecisionStatus
from .errors import InvalidDecisionInputError

def utc_now_iso(): return datetime.now(timezone.utc).replace(microsecond=0).isoformat()
def _fm(v): return MappingProxyType(dict(sorted((v or {}).items())))
def _tm(v): return tuple(v or ())

@dataclass(frozen=True, slots=True)
class DecisionPolicy:
    policy_id:str='executive-decision-policy-v1'; mission_alignment_weight:float=.30; evidence_strength_weight:float=.20; confidence_weight:float=.15; safety_weight:float=.15; resource_efficiency_weight:float=.10; time_utility_weight:float=.10; minimum_score:float=.50; minimum_confidence:float=.40; require_constitutional_pass:bool=True; require_authority:bool=True; strict_no_selection:bool=False; constitution_revision:str='CONST-0001/1.0'
    def __post_init__(self):
        weights=(self.mission_alignment_weight,self.evidence_strength_weight,self.confidence_weight,self.safety_weight,self.resource_efficiency_weight,self.time_utility_weight)
        if any(x<0 for x in weights) or abs(sum(weights)-1)>1e-9: raise InvalidDecisionInputError('Policy weights must be non-negative and sum to 1.0.')
        if not 0<=self.minimum_score<=1 or not 0<=self.minimum_confidence<=1: raise InvalidDecisionInputError('Policy thresholds must be between 0 and 1.')

@dataclass(frozen=True, slots=True)
class EvaluatedCourseOfAction:
    coa_id:str; title:str; mission_alignment:float; evidence_strength:float; confidence:float; safety:float; resource_efficiency:float; time_utility:float; constitutional_status:ConstitutionalStatus=ConstitutionalStatus.PASS; authority_status:AuthorityStatus=AuthorityStatus.AUTHORIZED; authority_reference:str=''; rationale:str=''; risk_summary:str=''; evidence_ids:Tuple[str,...]=field(default_factory=tuple); hypothesis_ids:Tuple[str,...]=field(default_factory=tuple); observation_ids:Tuple[str,...]=field(default_factory=tuple); metadata:Mapping[str,str]=field(default_factory=lambda:MappingProxyType({}))
    def __post_init__(self):
        if not self.coa_id.strip(): raise InvalidDecisionInputError('coa_id is required.')
        for n in ('mission_alignment','evidence_strength','confidence','safety','resource_efficiency','time_utility'):
            if not 0<=getattr(self,n)<=1: raise InvalidDecisionInputError(f'{n} must be between 0 and 1.')
        object.__setattr__(self,'evidence_ids',_tm(self.evidence_ids)); object.__setattr__(self,'hypothesis_ids',_tm(self.hypothesis_ids)); object.__setattr__(self,'observation_ids',_tm(self.observation_ids)); object.__setattr__(self,'metadata',_fm(self.metadata))

@dataclass(frozen=True, slots=True)
class CandidateAssessment:
    coa_id:str; score:float; confidence:float; disposition:CandidateDisposition; reasons:Tuple[str,...]=field(default_factory=tuple); component_scores:Mapping[str,float]=field(default_factory=lambda:MappingProxyType({}))
    def __post_init__(self): object.__setattr__(self,'reasons',_tm(self.reasons)); object.__setattr__(self,'component_scores',_fm(self.component_scores))

@dataclass(frozen=True, slots=True)
class DecisionTrace:
    policy_id:str; constitution_revision:str; candidate_ids:Tuple[str,...]; selected_coa_id:str|None; observation_ids:Tuple[str,...]; evidence_ids:Tuple[str,...]; hypothesis_ids:Tuple[str,...]; situation_reference:str; reasoning_reference:str
    def __post_init__(self):
        for n in ('candidate_ids','observation_ids','evidence_ids','hypothesis_ids'): object.__setattr__(self,n,tuple(sorted(set(getattr(self,n)))))

@dataclass(frozen=True, slots=True)
class ExecutiveDecision:
    decision_id:str; mission_id:str; status:DecisionStatus; selected_coa_id:str|None; confidence:float; explanation:str; assessments:Tuple[CandidateAssessment,...]; trace:DecisionTrace; created_at:str; policy_id:str; constitution_revision:str

@dataclass(frozen=True, slots=True)
class DecisionRequest:
    mission_id:str; candidates:Tuple[EvaluatedCourseOfAction,...]; situation_reference:str=''; reasoning_reference:str=''; request_id:str=''
    def __post_init__(self):
        if not self.mission_id.strip() or not self.candidates: raise InvalidDecisionInputError('mission_id and at least one candidate are required.')
        ids=[x.coa_id for x in self.candidates]
        if len(ids)!=len(set(ids)): raise InvalidDecisionInputError('Candidate identifiers must be unique.')
        object.__setattr__(self,'candidates',tuple(self.candidates))
