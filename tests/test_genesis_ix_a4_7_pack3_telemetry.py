import unittest
from core.conversation.grounded_answer.telemetry import GroundedAnswerTelemetry, GroundedAnswerTelemetryStore

class Tests(unittest.TestCase):
    def test_empty(self):
        x=GroundedAnswerTelemetryStore().projection()
        self.assertFalse(x["available"])
    def test_publish(self):
        s=GroundedAnswerTelemetryStore()
        s.publish(GroundedAnswerTelemetry("now","r","s","q","partial",.55,2,3,2,0,"incomplete",None))
        x=s.projection(); self.assertEqual(x["accepted_evidence"],2); self.assertEqual(x["rejected_evidence"],3)
    def test_clamp(self):
        x=GroundedAnswerTelemetry("now","r","s","q","known",4,1,0,1,0,"",None)
        self.assertEqual(x.confidence,1.0)
    def test_clear(self):
        s=GroundedAnswerTelemetryStore()
        s.publish(GroundedAnswerTelemetry("now","r","s","q","unknown",0,0,1,0,0,"unknown","acquire"))
        s.clear(); self.assertFalse(s.projection()["available"])
if __name__=="__main__": unittest.main()
