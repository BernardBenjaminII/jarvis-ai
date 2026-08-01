from __future__ import annotations
from collections import defaultdict
from typing import Any
from .contracts import CoverageClassification, RepositoryCoverageStatus
from .fingerprints import canonical_fingerprint
from .models import ArticleCoverageMetric,CoveragePolicy,CoverageStatistics,DomainCoverageMetric

def build_article_metrics(article_usage:list[dict[str,Any]],policy:CoveragePolicy):
    out=[]
    for item in sorted(article_usage,key=lambda v:str(v.get("article_id",""))):
        aid=str(item.get("article_id","")); refs=int(item.get("reference_count",0)); comp=int(item.get("compliant_count",0)); rev=int(item.get("review_required_count",0)); non=int(item.get("noncompliant_count",0)); ids=item.get("artifact_ids",[]); count=len(ids) if isinstance(ids,list) else 0
        cls=CoverageClassification.UNUSED.value if refs==0 else (CoverageClassification.UNDERUTILIZED.value if refs<=policy.low_usage_threshold else CoverageClassification.EXERCISED.value)
        score=round(min(1.0,(refs+comp+rev*0.5+non*0.25)/max(1,policy.low_usage_threshold*4)),6)
        basis={"article_id":aid,"reference_count":refs,"compliant_count":comp,"review_required_count":rev,"noncompliant_count":non,"artifact_count":count,"classification":cls,"influence_score":score}
        out.append(ArticleCoverageMetric(**basis,metric_fingerprint=canonical_fingerprint(basis)))
    return tuple(out)

def build_domain_metrics(artifacts,assessments,policy):
    domain_by={str(x.get("artifact_id","")):str(x.get("domain","general")) for x in artifacts}; totals=defaultdict(int); applicable=defaultdict(int)
    for x in artifacts: totals[str(x.get("domain","general"))]+=1
    for x in assessments:
        d=domain_by.get(str(x.get("artifact_id","")),"general")
        if str(x.get("overall_status",""))!="not_applicable": applicable[d]+=1
    out=[]
    for d in sorted(set(totals)|set(policy.governed_domains)):
        total=totals.get(d,0); app=applicable.get(d,0); ratio=round(app/total,6) if total else 0.0
        status=RepositoryCoverageStatus.GOVERNED.value if ratio>=policy.governed_domain_coverage_threshold else (RepositoryCoverageStatus.PARTIALLY_GOVERNED.value if ratio>=policy.partial_domain_coverage_threshold else RepositoryCoverageStatus.UNGOVERNED.value)
        basis={"domain":d,"artifacts_total":total,"artifacts_applicable":app,"artifacts_not_applicable":max(0,total-app),"coverage_ratio":ratio,"status":status}
        out.append(DomainCoverageMetric(**basis,metric_fingerprint=canonical_fingerprint(basis)))
    return tuple(out)

def build_statistics(article_metrics,domain_metrics,artifacts_total,artifacts_governed):
    ex=sum(x.classification=="exercised" for x in article_metrics); under=sum(x.classification=="underutilized" for x in article_metrics); unused=sum(x.classification=="unused" for x in article_metrics)
    dg=sum(x.status=="governed" for x in domain_metrics); dp=sum(x.status=="partially_governed" for x in domain_metrics); du=sum(x.status=="ungoverned" for x in domain_metrics)
    return CoverageStatistics(len(article_metrics),ex,under,unused,artifacts_total,artifacts_governed,max(0,artifacts_total-artifacts_governed),len(domain_metrics),dg,dp,du,round((ex+under)/len(article_metrics),6) if article_metrics else 0.0,round(artifacts_governed/artifacts_total,6) if artifacts_total else 0.0)
