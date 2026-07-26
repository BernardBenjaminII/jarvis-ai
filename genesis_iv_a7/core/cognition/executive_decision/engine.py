from __future__ import annotations
import hashlib,json
from dataclasses import replace
from .contracts import CandidateAssessment,DecisionPolicy,DecisionRequest,DecisionTrace,ExecutiveDecision,utc_now_iso
from .enums import AuthorityStatus,CandidateDisposition,ConstitutionalStatus,DecisionStatus
from .errors import NoAdmissibleCourseOfActionError
from .scoring import component_scores,weighted_score

class ExecutiveDecisionEngine:
    def __init__(self,policy=None): self._policy=policy or DecisionPolicy()
    @property
    def policy(self): return self._policy
    def assess(self,c):
        s=weighted_score(c,self._policy); r=[]
        if self._policy.require_constitutional_pass and c.constitutional_status is not ConstitutionalStatus.PASS: d=CandidateDisposition.REJECTED_CONSTITUTION; r.append('Constitutional compliance failed.')
        elif self._policy.require_authority and c.authority_status is not AuthorityStatus.AUTHORIZED: d=CandidateDisposition.REJECTED_AUTHORITY; r.append('Required authority was not established.')
        elif c.confidence<self._policy.minimum_confidence or s<self._policy.minimum_score: d=CandidateDisposition.REJECTED_THRESHOLD; r.append('Candidate did not satisfy policy thresholds.')
        else: d=CandidateDisposition.ELIGIBLE; r.append('Candidate satisfies all decision gates.')
        return CandidateAssessment(c.coa_id,s,c.confidence,d,tuple(r),component_scores(c))
    def rank(self,candidates): return tuple(sorted((self.assess(c) for c in candidates),key=lambda x:(0 if x.disposition is CandidateDisposition.ELIGIBLE else 1,-x.score,-x.confidence,x.coa_id)))
    def decide(self,request):
        ranked=self.rank(request.candidates); eligible=[x for x in ranked if x.disposition is CandidateDisposition.ELIGIBLE]; selected=eligible[0].coa_id if eligible else None
        if selected is None and self._policy.strict_no_selection: raise NoAdmissibleCourseOfActionError('No candidate is admissible.')
        final=[]
        for x in ranked:
            if x.coa_id==selected: final.append(replace(x,disposition=CandidateDisposition.SELECTED,reasons=x.reasons+('Highest-ranked admissible candidate.',)))
            elif x.disposition is CandidateDisposition.ELIGIBLE: final.append(replace(x,disposition=CandidateDisposition.NOT_SELECTED,reasons=x.reasons+('A higher-ranked admissible candidate was selected.',)))
            else: final.append(x)
        trace=self._trace(request,selected); did=self._id(request,tuple(final),selected); conf=next((x.confidence for x in final if x.coa_id==selected),0.0)
        expl=(f'Mission {request.mission_id}: selected {selected}.' if selected else f'Mission {request.mission_id}: no admissible Course of Action; the Executive abstained.')
        return ExecutiveDecision(did,request.mission_id,DecisionStatus.SELECTED if selected else DecisionStatus.ABSTAINED,selected,conf,expl,tuple(final),trace,utc_now_iso(),self._policy.policy_id,self._policy.constitution_revision)
    def _trace(self,r,s):
        o=set();e=set();h=set()
        for c in r.candidates: o.update(c.observation_ids);e.update(c.evidence_ids);h.update(c.hypothesis_ids)
        return DecisionTrace(self._policy.policy_id,self._policy.constitution_revision,tuple(c.coa_id for c in r.candidates),s,tuple(o),tuple(e),tuple(h),r.situation_reference,r.reasoning_reference)
    def _id(self,r,a,s):
        p={'mission_id':r.mission_id,'request_id':r.request_id,'policy_id':self._policy.policy_id,'constitution_revision':self._policy.constitution_revision,'selected':s,'assessments':[{'coa_id':x.coa_id,'score':x.score,'confidence':x.confidence,'disposition':x.disposition.value} for x in a]}
        return 'decision-'+hashlib.sha256(json.dumps(p,sort_keys=True,separators=(',',':')).encode()).hexdigest()[:24]
