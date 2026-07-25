from __future__ import annotations
import unittest
from datetime import datetime, timezone
from core.cognition.observation import *

T=datetime(2026,7,24,tzinfo=timezone.utc)

def make(value=91):
    p=ObservationProvenance.create(producer="runtime",source="ubuntu",authority=SourceAuthority.SYSTEM)
    return Observation.create(observation_type="runtime.cpu",kind=ObservationKind.TELEMETRY,
                              value=value,provenance=p,occurred_at=T,confidence=.99,
                              severity=ObservationSeverity.WARNING,mission_id="m1")

class Tests(unittest.TestCase):
    def test_deterministic_identity(self):
        self.assertEqual(make().observation_id,make().observation_id)
    def test_invalid_confidence(self):
        p=ObservationProvenance.create(producer="x",source="y")
        with self.assertRaises(InvalidObservationError):
            Observation.create(observation_type="x",kind=ObservationKind.STATE,value=1,provenance=p,occurred_at=T,confidence=2)
    def test_repository_and_query(self):
        r=InMemoryObservationRepository(); a=make(1); b=make(2)
        self.assertTrue(r.append(a)); self.assertFalse(r.append(a)); self.assertTrue(r.append(b))
        self.assertEqual(len(r.query(ObservationQuery(observation_type="runtime.cpu"))),2)
    def test_bus_duplicate_and_order(self):
        r=InMemoryObservationRepository(); bus=ExecutiveObservationBus(r); seen=[]
        bus.subscribe("z",lambda o:seen.append("z")); bus.subscribe("a",lambda o:seen.append("a"))
        a=make(); self.assertTrue(bus.publish(a).accepted); self.assertTrue(bus.publish(a).duplicate)
        self.assertEqual(seen,["a","z"])
    def test_service(self):
        r=InMemoryObservationRepository(); s=ExecutiveObservationService(ExecutiveObservationBus(r))
        receipt=s.record(observation_type="knowledge.coverage",kind=ObservationKind.KNOWLEDGE,value={"coverage":.82},
                         producer="catalog",source="catalog.sqlite",occurred_at=T,authority=SourceAuthority.SYSTEM)
        self.assertTrue(receipt.accepted); self.assertEqual(r.count(),1)

if __name__=="__main__": unittest.main()
