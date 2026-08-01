from __future__ import annotations
import json
from pathlib import Path
from .models import CanonicalConstitution

class ConstitutionalRatificationReporter:
    def write(self,c:CanonicalConstitution,output_directory:Path):
        output_directory.mkdir(parents=True,exist_ok=True)
        registry={"schema_version":c.schema_version,"repository_fingerprint":c.repository_fingerprint,
                  "extraction_fingerprint":c.extraction_fingerprint,"analysis_fingerprint":c.analysis_fingerprint,
                  "ratification_fingerprint":c.ratification_fingerprint,
                  "articles":[a.to_dict() for a in c.articles]}
        sections={"ratification_fingerprint":c.ratification_fingerprint,"sections":[s.to_dict() for s in c.sections]}
        trace={"ratification_fingerprint":c.ratification_fingerprint,"records":[t.to_dict() for t in c.traceability]}
        by_source={}
        for a in c.articles:
            for source in a.supporting_source_paths: by_source.setdefault(source,set()).add(a.article_id)
        index={"ratification_fingerprint":c.ratification_fingerprint,
               "by_domain":{s.domain:list(s.article_ids) for s in c.sections},
               "by_status":{status:[a.article_id for a in c.articles if a.status==status]
                            for status in ("ratified","review_required","rejected")},
               "by_source":{k:sorted(v) for k,v in sorted(by_source.items())}}
        summary=c.to_dict()
        for key in ("articles","sections","traceability"): summary.pop(key)
        artifacts={
            "constitutional_ratification.json":summary,
            "constitutional_articles.json":registry,
            "constitutional_sections.json":sections,
            "constitutional_registry.json":registry,
            "constitutional_index.json":index,
            "constitutional_traceability.json":trace,
        }
        written=[]
        for name,payload in artifacts.items():
            path=output_directory/name
            path.write_text(json.dumps(payload,indent=2,sort_keys=True,ensure_ascii=False)+"\n",encoding="utf-8")
            written.append(path)
        s=c.statistics
        report=output_directory/"constitutional_ratification_report.md"
        report.write_text("\n".join([
            "# Genesis VII-C3 Constitutional Ratification Report","",
            f"**Repository fingerprint:** `{c.repository_fingerprint}`",
            f"**Extraction fingerprint:** `{c.extraction_fingerprint}`",
            f"**Analysis fingerprint:** `{c.analysis_fingerprint}`",
            f"**Ratification fingerprint:** `{c.ratification_fingerprint}`","",
            "## Statistics","",f"- Claims: {s.claims}",f"- Clusters: {s.clusters}",
            f"- Articles: {s.articles}",f"- Ratified articles: {s.ratified_articles}",
            f"- Review-required articles: {s.review_required_articles}",
            f"- Rejected articles: {s.rejected_articles}",f"- Sections: {s.sections}",
            f"- Traced claims: {s.traced_claims}",f"- Unrepresented claims: {s.unrepresented_claims}",
            f"- Diagnostics: {s.diagnostics}","","## Governance boundary","",
            "Ratified status means the cluster satisfied the deterministic C3 policy.",
            "Formal constitutional adoption remains a Commander-governed act.",""
        ]),encoding="utf-8")
        written.append(report)
        return tuple(written)
