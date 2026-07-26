from dataclasses import FrozenInstanceError,dataclass
from datetime import datetime,timezone
import unittest
from core.observation import *
T=datetime(2026,7,26,8,0,tzinfo=timezone.utc)
def source():
    return ObservationSource.create(reality_class=RealityClass.RECORDED,source_type=SourceType.BOOK,identifier="book:strategy",kind="epub",producer="academy-reader",collector="document-extractor",authority=SourceAuthority.PRIMARY,segment_id="chapter-2",start_offset=10,end_offset=80,excerpt="Strategy connects purpose and action.")
def make(recorded_at=T):
    return Observation.create(domain=ObservationDomain.KNOWLEDGE,observation_type="knowledge.definition",kind=ObservationKind.CONTENT,subject="strategy",predicate="is_defined_as",value="connection of purpose and action",source=source(),observed_at=T,recorded_at=recorded_at,confidence=.97,statement="The source defines strategy.")
class Tests(unittest.TestCase):
    def test_recorded_reality(self): self.assertEqual(make().source.reality_class,RealityClass.RECORDED)
    def test_book_source(self): self.assertEqual(make().source.source_type,SourceType.BOOK)
    def test_deterministic_identity(self): self.assertEqual(make().observation_id,make().observation_id)
    def test_recorded_time_excluded_from_identity(self): self.assertEqual(make(T).observation_id,make(datetime(2026,7,26,9,tzinfo=timezone.utc)).observation_id)
    def test_immutable(self):
        with self.assertRaises(FrozenInstanceError): make().confidence=.1
    def test_invalid_confidence(self):
        with self.assertRaises(ObservationValidationError): Observation.create(domain="system",observation_type="system.bad",kind="state",subject="system",predicate="reports",value=True,source=source(),observed_at=T,confidence=2)
    def test_naive_time_rejected(self):
        with self.assertRaises(ObservationSerializationError): Observation.create(domain="system",observation_type="system.bad",kind="state",subject="system",predicate="reports",value=True,source=source(),observed_at=datetime(2026,7,26,8))
    def test_severity_priority_separate(self):
        o=Observation.create(domain="platform",observation_type="platform.disk",kind="telemetry",subject="root",predicate="usage",value=92,source=ObservationSource.create(reality_class="live",source_type="platform",identifier="ubuntu"),observed_at=T,severity="warning",priority="high")
        self.assertEqual((o.severity,o.priority),(ObservationSeverity.WARNING,ObservationPriority.HIGH))
    def test_supersession(self):
        a=make(); b=Observation.create(domain=a.domain,observation_type=a.observation_type,kind=a.kind,subject=a.subject,predicate=a.predicate,value="corrected",source=a.source,observed_at=T,supersedes_observation_id=a.observation_id)
        self.assertNotEqual(a.observation_id,b.observation_id)
    def test_legacy_adapter(self):
        @dataclass(frozen=True)
        class P: producer:str="runtime"; source:str="ubuntu"; authority:str="system"
        @dataclass(frozen=True)
        class L: observation_type:str="platform.cpu"; kind:str="telemetry"; value:int=91; provenance:P=P(); occurred_at:datetime=T; confidence:float=.99; severity:str="warning"; mission_id:str="m1"; observation_id:str="old"
        o=adapt_legacy_observation(L()); self.assertEqual((o.domain,o.context.mission_id),(ObservationDomain.PLATFORM,"m1"))
if __name__=="__main__": unittest.main()
