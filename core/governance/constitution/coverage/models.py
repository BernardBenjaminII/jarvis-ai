from __future__ import annotations
from dataclasses import asdict, dataclass
from typing import Any

@dataclass(frozen=True)
class CoveragePolicy:
    low_usage_threshold:int
    partial_domain_coverage_threshold:float
    governed_domain_coverage_threshold:float
    governed_domains:tuple[str,...]
    def to_dict(self)->dict[str,Any]:
        v=asdict(self); v["governed_domains"]=list(self.governed_domains); return v

@dataclass(frozen=True)
class ArticleCoverageMetric:
    article_id:str; reference_count:int; compliant_count:int; review_required_count:int; noncompliant_count:int; artifact_count:int; classification:str; influence_score:float; metric_fingerprint:str
    def to_dict(self)->dict[str,Any]: return asdict(self)

@dataclass(frozen=True)
class DomainCoverageMetric:
    domain:str; artifacts_total:int; artifacts_applicable:int; artifacts_not_applicable:int; coverage_ratio:float; status:str; metric_fingerprint:str
    def to_dict(self)->dict[str,Any]: return asdict(self)

@dataclass(frozen=True)
class CoverageStatistics:
    articles_total:int; articles_exercised:int; articles_underutilized:int; articles_unused:int; artifacts_total:int; artifacts_governed:int; artifacts_ungoverned:int; domains_total:int; domains_governed:int; domains_partially_governed:int; domains_ungoverned:int; article_coverage_ratio:float; repository_coverage_ratio:float
    def to_dict(self)->dict[str,Any]: return asdict(self)

@dataclass(frozen=True)
class ConstitutionalCoverageAssessment:
    schema_version:str; repository_fingerprint:str; extraction_fingerprint:str; analysis_fingerprint:str; ratification_fingerprint:str; compliance_fingerprint:str; certification_fingerprint:str; audit_fingerprint:str; coverage_fingerprint:str; policy:CoveragePolicy; article_metrics:tuple[ArticleCoverageMetric,...]; domain_metrics:tuple[DomainCoverageMetric,...]; statistics:CoverageStatistics; diagnostics:tuple[str,...]
    def to_dict(self)->dict[str,Any]:
        return {"schema_version":self.schema_version,"repository_fingerprint":self.repository_fingerprint,"extraction_fingerprint":self.extraction_fingerprint,"analysis_fingerprint":self.analysis_fingerprint,"ratification_fingerprint":self.ratification_fingerprint,"compliance_fingerprint":self.compliance_fingerprint,"certification_fingerprint":self.certification_fingerprint,"audit_fingerprint":self.audit_fingerprint,"coverage_fingerprint":self.coverage_fingerprint,"policy":self.policy.to_dict(),"article_metrics":[x.to_dict() for x in self.article_metrics],"domain_metrics":[x.to_dict() for x in self.domain_metrics],"statistics":self.statistics.to_dict(),"diagnostics":list(self.diagnostics)}
