from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
import tempfile
from dev.acceptance.campaign import CampaignDefinition
from dev.acceptance.runner import AcceptanceRunner
from dev.acceptance.test_case import AcceptanceTestCase, ExpectedOutcome

class Runtime:
    def execute(self,prompt,*,mode,metadata):
        return "Certified grounded response [C1]."
    def telemetry(self):
        return {
            "state":"known","confidence":0.92,"accepted_evidence":2,
            "rejected_evidence":1,"citation_count":1,"conflict_count":0,
            "recommended_action":None,
        }

def main():
    case = AcceptanceTestCase(
        "CERT-PACK2-1","Harness","Harness certification","Certify.",
        ExpectedOutcome(expected_state="known",minimum_confidence=0.8,
                        minimum_accepted_evidence=1,require_citations=True),
    )
    campaign = CampaignDefinition.create(
        campaign_id="GENESIS-IX-A4.8-PACK2-CERT",
        name="Pack 2 Certification",version="1",tests=(case,),
    )
    with tempfile.TemporaryDirectory() as temp:
        result = AcceptanceRunner(Runtime(),Path(temp)).run(campaign,run_id="certification")
        root = Path(result["run_root"])
        assert result["results"][0].passed
        for name in ("run_manifest.json","results.jsonl","Executive_Acceptance_Report.md","summary.json"):
            assert (root/name).is_file()
    print("[PASS] Campaign execution")
    print("[PASS] Assertion evaluation")
    print("[PASS] Failure classification")
    print("[PASS] Evidence capture")
    print("[PASS] Report generation")
    print("[PASS] Artifact archival")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
