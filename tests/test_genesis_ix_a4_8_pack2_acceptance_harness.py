import tempfile, unittest
from pathlib import Path
from dev.acceptance.campaign import CampaignDefinition
from dev.acceptance.classification import FailureClassification
from dev.acceptance.runner import AcceptanceRunner
from dev.acceptance.test_case import AcceptanceTestCase, ExpectedOutcome

class FakeRuntime:
    def __init__(self, state="known"):
        self.state = state
    def execute(self, prompt, *, mode, metadata):
        return "Supported answer [C1]."
    def telemetry(self):
        return {
            "available":True, "state":self.state,
            "confidence":0.9 if self.state=="known" else 0.0,
            "accepted_evidence":1 if self.state=="known" else 0,
            "rejected_evidence":0 if self.state=="known" else 2,
            "citation_count":1 if self.state=="known" else 0,
            "conflict_count":0,
            "recommended_action":None if self.state=="known" else "Acquire sources.",
        }

class Tests(unittest.TestCase):
    def campaign(self, case):
        return CampaignDefinition.create(campaign_id="test", name="Test", version="1", tests=(case,))

    def test_passing_campaign(self):
        case = AcceptanceTestCase(
            "PASS-1","Retrieval","Passing","Known question",
            ExpectedOutcome(expected_state="known",minimum_accepted_evidence=1,require_citations=True),
        )
        with tempfile.TemporaryDirectory() as temp:
            result = AcceptanceRunner(FakeRuntime(),Path(temp)).run(self.campaign(case),run_id="run-1")
            self.assertTrue(result["results"][0].passed)
            self.assertTrue((Path(result["run_root"])/"run_manifest.json").is_file())

    def test_failure_classification(self):
        case = AcceptanceTestCase(
            "FAIL-1","Gap Detection","Failing","Unknown question",
            ExpectedOutcome(expected_state="unknown"),
            classification_on_failure=FailureClassification.GROUNDING,
        )
        with tempfile.TemporaryDirectory() as temp:
            result = AcceptanceRunner(FakeRuntime("known"),Path(temp)).run(self.campaign(case),run_id="run-2")
            item = result["results"][0]
            self.assertFalse(item.passed)
            self.assertEqual(item.classification,FailureClassification.GROUNDING)

    def test_required_artifacts(self):
        case = AcceptanceTestCase("ART-1","Conversation","Artifacts","Q",ExpectedOutcome())
        with tempfile.TemporaryDirectory() as temp:
            result = AcceptanceRunner(FakeRuntime(),Path(temp)).run(self.campaign(case),run_id="run-3")
            root = Path(result["run_root"])
            for name in (
                "results.jsonl","failures.jsonl","Executive_Acceptance_Report.md",
                "Executive_Runtime_Scorecard.md","Capability_Matrix.md",
                "summary.json","run_manifest.json",
            ):
                self.assertTrue((root/name).is_file(),name)

    def test_unknown_pass(self):
        case = AcceptanceTestCase(
            "GAP-1","Gap Detection","Unknown","Warp core",
            ExpectedOutcome(expected_state="unknown",maximum_accepted_evidence=0,require_recommendation=True),
        )
        with tempfile.TemporaryDirectory() as temp:
            result = AcceptanceRunner(FakeRuntime("unknown"),Path(temp)).run(self.campaign(case),run_id="run-4")
            self.assertTrue(result["results"][0].passed)

if __name__ == "__main__":
    unittest.main()
