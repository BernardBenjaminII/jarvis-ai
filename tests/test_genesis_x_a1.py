import sqlite3,tempfile,unittest
from pathlib import Path
from core.knowledge_catalog.production_materialization.checkpoint import CheckpointStore
from core.knowledge_catalog.production_materialization.models import WorkItem,MaterializationStage

class Tests(unittest.TestCase):
    def test_checkpoint_resume(self):
        with tempfile.TemporaryDirectory() as t:
            s=CheckpointStore(Path(t)/"c.sqlite")
            item=WorkItem("id:1","/tmp/a.txt","A",None,".txt")
            self.assertEqual(s.register((item,)),1)
            self.assertEqual(s.register((item,)),0)
            self.assertEqual(len(s.next_items(10)),1)
    def test_stage_transition(self):
        with tempfile.TemporaryDirectory() as t:
            s=CheckpointStore(Path(t)/"c.sqlite")
            item=WorkItem("id:1","/tmp/a.txt","A",None,".txt")
            s.register((item,)); s.set_stage(item.candidate_id,MaterializationStage.VALIDATED,"ok")
            self.assertEqual(s.counts()["VALIDATED"],1)
    def test_checkpoint_separate(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t); prod=root/"runtime.sqlite"; sqlite3.connect(prod).close(); before=prod.read_bytes()
            CheckpointStore(root/"checkpoint.sqlite")
            self.assertEqual(before,prod.read_bytes())
if __name__=="__main__": unittest.main()
