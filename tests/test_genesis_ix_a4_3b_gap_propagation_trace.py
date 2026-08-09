from __future__ import annotations
from dataclasses import dataclass
import tempfile
from pathlib import Path
import unittest
from core.retrieval.gap_trace import KnowledgeGapPropagationTracer, extract_gap_state

@dataclass
class Gap:
    recommended_action:str
    def to_dict(self): return {"recommended_action":self.recommended_action}

@dataclass
class Grounding:
    gaps:tuple[Gap,...]
    status:str
    def to_dict(self): return {"gaps":[x.to_dict() for x in self.gaps],"status":self.status}

class Tests(unittest.TestCase):
    def test_extract_gap(self):
        state=extract_gap_state(Grounding((Gap("Acquire sources."),),"gap"))
        self.assertTrue(state["gap_present"])
        self.assertEqual(state["gap_count"],1)

    def test_no_gap(self):
        state=extract_gap_state({"gaps":[],"status":"grounded"})
        self.assertFalse(state["gap_present"])

    def test_objective_gap(self):
        state=extract_gap_state({"objectives":[{"gap":{"recommended_action":"Queue acquisition."}}]})
        self.assertTrue(state["gap_present"])

    def test_empty_verdict(self):
        with tempfile.TemporaryDirectory() as d:
            tracer=KnowledgeGapPropagationTracer(Path(d),None)
            self.assertEqual(tracer._verdict()["classification"],"CONFIGURATION_DEFECT")

    def test_missing_sources(self):
        with tempfile.TemporaryDirectory() as d:
            tracer=KnowledgeGapPropagationTracer(Path(d),None)
            self.assertFalse(tracer._source_locations()["grounding"]["exists"])

if __name__=="__main__": unittest.main()
