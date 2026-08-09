from __future__ import annotations
import json, time, uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from .archive import archive_results
from .capture import AcceptanceCapture
from .classification import FailureClassification
from .reporting import write_reports
from .result import AcceptanceResult, AcceptanceStatus

def utc_now():
    return datetime.now(timezone.utc).isoformat()

@dataclass(slots=True)
class AcceptanceRunner:
    runtime: object
    output_root: Path

    def run(self, campaign, *, run_id=None):
        run_id = run_id or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"-"+uuid.uuid4().hex[:8]
        root = self.output_root / run_id
        root.mkdir(parents=True, exist_ok=True)
        capture = AcceptanceCapture(root)
        started = utc_now()
        results = [self._run_test(run_id, case, capture) for case in campaign.tests]
        summary = write_reports(root, results)
        archive = archive_results(root, results)
        manifest = {
            "schema_version":"genesis_ix_a4_8_pack2_v1",
            "run_id":run_id, "campaign_id":campaign.campaign_id,
            "campaign_name":campaign.name, "campaign_version":campaign.version,
            "started_at":started, "completed_at":utc_now(),
            "tests_executed":len(results), "summary":summary, "archive":archive,
        }
        (root/"run_manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True)+"\n", encoding="utf-8")
        return {"run_root":str(root), "manifest":manifest, "results":tuple(results)}

    def _run_test(self, run_id, case, capture):
        start_at, start_ns = utc_now(), time.perf_counter_ns()
        answer, telemetry, assertions, error = "", {}, [], None
        status = AcceptanceStatus.PASS
        prompt_path = capture.capture_prompt(case.test_id, case.prompt)
        try:
            answer = self.runtime.execute(
                case.prompt, mode=case.mode,
                metadata={"acceptance_run_id":run_id,"acceptance_test_id":case.test_id,**dict(case.metadata)}
            )
            telemetry = self.runtime.telemetry()
            assertions = self._evaluate(case, answer, telemetry)
            if any(x["status"]=="FAIL" for x in assertions):
                status = AcceptanceStatus.FAIL
        except Exception as exc:
            status = AcceptanceStatus.ERROR
            error = f"{type(exc).__name__}: {exc}"
        duration = (time.perf_counter_ns()-start_ns)/1_000_000
        response_path = capture.capture_response(case.test_id, answer)
        telemetry_path = capture.capture_telemetry(case.test_id, telemetry)
        trace_path = capture.capture_trace(case.test_id, {"assertions":assertions,"error":error})
        classification = None if status is AcceptanceStatus.PASS else (
            case.classification_on_failure if status is AcceptanceStatus.FAIL else FailureClassification.RUNTIME
        )
        severity = None if status is AcceptanceStatus.PASS else case.severity_on_failure
        return AcceptanceResult(
            run_id, case.test_id, case.domain, status, start_at, utc_now(),
            duration, answer, telemetry.get("state"), telemetry.get("confidence"),
            telemetry.get("accepted_evidence"), telemetry.get("rejected_evidence"),
            telemetry.get("citation_count"), telemetry.get("conflict_count"),
            telemetry.get("recommended_action"), tuple(assertions),
            classification, severity, error, telemetry,
            {"prompt_path":prompt_path,"response_path":response_path,
             "telemetry_path":telemetry_path,"trace_path":trace_path},
        )

    @staticmethod
    def _evaluate(case, answer, telemetry):
        e, checks = case.expected, []
        def add(code, passed, observed, expected):
            checks.append({"code":code,"status":"PASS" if passed else "FAIL","observed":observed,"expected":expected})
        if e.require_answer_text:
            add("ANSWER-TEXT", bool(answer.strip()), bool(answer.strip()), True)
        if e.expected_state is not None:
            add("STATE", telemetry.get("state")==e.expected_state, telemetry.get("state"), e.expected_state)
        c = telemetry.get("confidence")
        if e.minimum_confidence is not None:
            add("CONFIDENCE-MIN", c is not None and float(c)>=e.minimum_confidence, c, e.minimum_confidence)
        if e.maximum_confidence is not None:
            add("CONFIDENCE-MAX", c is not None and float(c)<=e.maximum_confidence, c, e.maximum_confidence)
        a = telemetry.get("accepted_evidence")
        if e.minimum_accepted_evidence is not None:
            add("ACCEPTED-MIN", a is not None and int(a)>=e.minimum_accepted_evidence, a, e.minimum_accepted_evidence)
        if e.maximum_accepted_evidence is not None:
            add("ACCEPTED-MAX", a is not None and int(a)<=e.maximum_accepted_evidence, a, e.maximum_accepted_evidence)
        r = telemetry.get("rejected_evidence")
        if e.minimum_rejected_evidence is not None:
            add("REJECTED-MIN", r is not None and int(r)>=e.minimum_rejected_evidence, r, e.minimum_rejected_evidence)
        if e.require_recommendation is not None:
            observed = bool(telemetry.get("recommended_action"))
            add("RECOMMENDATION", observed==e.require_recommendation, observed, e.require_recommendation)
        if e.require_citations is not None:
            observed = int(telemetry.get("citation_count") or 0)>0
            add("CITATIONS", observed==e.require_citations, observed, e.require_citations)
        folded = answer.casefold()
        for phrase in e.required_phrases:
            add("REQUIRED-"+phrase, phrase.casefold() in folded, phrase.casefold() in folded, True)
        for phrase in e.forbidden_phrases:
            add("FORBIDDEN-"+phrase, phrase.casefold() not in folded, phrase.casefold() in folded, False)
        return checks
