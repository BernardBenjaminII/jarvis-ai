from collections import Counter
from .contracts import ProbeForensicResult, RuntimeForensicReport
from .extract import candidate_record, mapping, number
from .probes import canonical_runtime_probes
from .provider import LiveQualificationProvider

class RuntimeQualificationForensics:
    def __init__(self, *, database_path, provider=None, probes=None, limit=10):
        self.database_path=database_path
        self.provider=provider or LiveQualificationProvider()
        self.probes=tuple(probes or canonical_runtime_probes())
        self.limit=limit

    def execute(self):
        results=[]
        global_reasons=Counter()
        for probe in self.probes:
            item=self._run_probe(probe)
            results.append(item)
            global_reasons.update(
                c.rejection_reason for c in item.candidates if c.rejection_reason
            )
        known=[x for x in results if x.expectation=="known"]
        raw_hits=sum(x.raw_count>0 for x in known)
        qualified_hits=sum(x.qualified_count>0 for x in known)
        raw_recall=0.0 if not known else raw_hits/len(known)
        qualified_recall=0.0 if not known else qualified_hits/len(known)
        summary={
            "known_probe_count":len(known),
            "known_raw_hits":raw_hits,
            "known_qualified_hits":qualified_hits,
            "known_raw_recall":raw_recall,
            "known_qualified_recall":qualified_recall,
            "rejection_reasons":dict(sorted(global_reasons.items())),
            "top_failure":global_reasons.most_common(1)[0][0] if global_reasons else None,
            "probe_error_count":sum(bool(x.raw_error or x.qualified_error) for x in results),
        }
        classification=self._classify(summary)
        status="EXCELLENT" if classification=="QUALIFICATION_RECALL_OPERATIONAL" else "FAILED"
        return RuntimeForensicReport(
            status,classification,tuple(results),summary,
            (
                "Do not modify qualification behavior until candidate diagnostics are reviewed.",
                "Promote each known probe into permanent regression coverage.",
                f"Prioritize the dominant rejection class: {summary['top_failure']}."
                if summary["top_failure"] else
                "Capture richer runtime diagnostics before tuning.",
            )
        )

    def _run_probe(self, probe):
        raw_rows=[]
        qualified_rows=[]
        raw_error=None
        qualified_error=None
        try:
            raw_rows=self.provider.raw_search(probe.query,database_path=self.database_path,limit=self.limit)
        except Exception as exc:
            raw_error=f"{type(exc).__name__}: {exc}"
        try:
            qualified_rows=self.provider.qualified_search(probe.query,database_path=self.database_path,limit=self.limit)
        except Exception as exc:
            qualified_error=f"{type(exc).__name__}: {exc}"
        trace=mapping(self.provider.last_trace())
        result=mapping(self.provider.last_result())
        threshold=number(trace.get("threshold"))
        if threshold is None: threshold=number(result.get("threshold"))
        diagnostics=trace.get("diagnostics")
        if not isinstance(diagnostics,(list,tuple)): diagnostics=result.get("diagnostics")
        if not isinstance(diagnostics,(list,tuple)): diagnostics=()
        source=list(diagnostics) or list(qualified_rows) or list(raw_rows)
        candidates=tuple(candidate_record(row,raw_rank=i,threshold=threshold) for i,row in enumerate(source,1))
        reasons=Counter(c.rejection_reason for c in candidates if c.rejection_reason)
        dominant=reasons.most_common(1)[0][0] if reasons else None
        if len(raw_rows)==0:
            recommendations=("Repair retrieval for this query before tuning qualification.",)
        elif len(qualified_rows)>0:
            recommendations=("Preserve the accepted path as permanent regression coverage.",)
        elif not diagnostics:
            recommendations=(
                "Expose complete qualification diagnostics for raw candidates.",
                "Do not tune thresholds from incomplete trace data.",
            )
        else:
            recommendations=(f"Investigate dominant rejection class: {dominant or 'UNKNOWN'}.",)
        return ProbeForensicResult(
            probe.probe_id,probe.query,probe.expectation,len(raw_rows),len(qualified_rows),
            raw_error,qualified_error,candidates,dominant,recommendations
        )

    @staticmethod
    def _classify(summary):
        if summary["probe_error_count"]: return "RUNTIME_FORENSIC_PROBE_ERRORS"
        raw=float(summary["known_raw_recall"])
        qualified=float(summary["known_qualified_recall"])
        if raw==0.0: return "RETRIEVAL_FAILURE_PRECEDES_QUALIFICATION"
        if qualified==0.0: return "QUALIFICATION_REJECTS_ALL_KNOWN_PROBES"
        if qualified<0.5: return "QUALIFICATION_RECALL_CRITICAL"
        if qualified<0.8: return "QUALIFICATION_RECALL_DEGRADED"
        return "QUALIFICATION_RECALL_OPERATIONAL"
