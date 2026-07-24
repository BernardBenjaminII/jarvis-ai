from __future__ import annotations
from dataclasses import FrozenInstanceError
from datetime import datetime, timezone
import unittest
from uuid import UUID, uuid4
from core.cognition.common.object_model import CognitiveLifecycleState,CognitiveObject,CognitiveObjectKind,InvalidConfidenceError,ProvenanceReference

class GenesisIVR1Tests(unittest.TestCase):
    def test_default(self):
        item=CognitiveObject(); self.assertIsInstance(item.object_id, UUID); self.assertEqual(item.kind,CognitiveObjectKind.GENERIC)
    def test_immutable(self):
        item=CognitiveObject()
        with self.assertRaises(FrozenInstanceError): item.confidence=0.5
    def test_confidence(self):
        with self.assertRaises(InvalidConfidenceError): CognitiveObject(confidence=1.01)
    def test_timezone(self):
        with self.assertRaises(ValueError): CognitiveObject(created_at=datetime(2026,1,1))
    def test_attributes_immutable(self):
        item=CognitiveObject(attributes={'mission':'alpha'})
        with self.assertRaises(TypeError): item.attributes['mission']='beta'
    def test_provenance(self):
        src=ProvenanceReference('document-1','document','page:2',{'title':'Example'})
        self.assertEqual(CognitiveObject(provenance=(src,)).to_primitive()['provenance'][0]['source_id'],'document-1')
    def test_deterministic(self):
        oid=uuid4(); ts=datetime(2026,7,21,tzinfo=timezone.utc)
        a=CognitiveObject(object_id=oid,created_at=ts,attributes={'b':2,'a':1})
        b=CognitiveObject(object_id=oid,created_at=ts,attributes={'a':1,'b':2})
        self.assertEqual(a.deterministic_hash,b.deterministic_hash)
    def test_compatibility(self):
        from core.cognition.common.cognitive_object import CognitiveObject as Alias
        self.assertIs(Alias,CognitiveObject)
if __name__=='__main__': unittest.main()
