from pathlib import Path
from .contracts import COVERAGE_INTELLIGENCE_SCHEMA_VERSION
from .fingerprints import canonical_fingerprint
from .inventory import load_repository_audit
from .metrics import build_article_metrics,build_domain_metrics,build_statistics
from .models import ConstitutionalCoverageAssessment,CoveragePolicy
from .policies import default_coverage_policy
class ConstitutionalCoverageIntelligenceEngine:
    def assess(self,*,audit_directory:Path,policy:CoveragePolicy|None=None):
        p=policy or default_coverage_policy(); audit,usage,inventory=load_repository_audit(audit_directory); artifacts=inventory.get("artifacts",[]); assessments=audit.get("assessments",[]); records=usage.get("article_usage",[]); diagnostics=[]
        if not isinstance(artifacts,list): artifacts=[]; diagnostics.append("Repository artifact inventory is invalid.")
        if not isinstance(assessments,list): assessments=[]; diagnostics.append("Repository assessments are invalid.")
        if not isinstance(records,list): records=[]; diagnostics.append("Article usage registry is invalid.")
        am=build_article_metrics(records,p); dm=build_domain_metrics(artifacts,assessments,p); governed=sum(str(x.get("overall_status",""))!="not_applicable" for x in assessments); stats=build_statistics(am,dm,len(artifacts),governed)
        if len(assessments)!=len(artifacts): diagnostics.append("Repository artifact and assessment counts differ.")
        if stats.articles_total==0: diagnostics.append("No constitutional article coverage records exist.")
        basis={"schema_version":COVERAGE_INTELLIGENCE_SCHEMA_VERSION,"repository_fingerprint":str(audit.get("repository_fingerprint","")),"extraction_fingerprint":str(audit.get("extraction_fingerprint","")),"analysis_fingerprint":str(audit.get("analysis_fingerprint","")),"ratification_fingerprint":str(audit.get("ratification_fingerprint","")),"compliance_fingerprint":str(audit.get("compliance_fingerprint","")),"certification_fingerprint":str(audit.get("certification_fingerprint","")),"audit_fingerprint":str(audit.get("audit_fingerprint","")),"policy":p.to_dict(),"article_metrics":[x.to_dict() for x in am],"domain_metrics":[x.to_dict() for x in dm],"statistics":stats.to_dict(),"diagnostics":diagnostics}
        return ConstitutionalCoverageAssessment(COVERAGE_INTELLIGENCE_SCHEMA_VERSION,basis["repository_fingerprint"],basis["extraction_fingerprint"],basis["analysis_fingerprint"],basis["ratification_fingerprint"],basis["compliance_fingerprint"],basis["certification_fingerprint"],basis["audit_fingerprint"],canonical_fingerprint(basis),p,am,dm,stats,tuple(diagnostics))
