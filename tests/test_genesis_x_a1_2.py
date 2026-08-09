import unittest
from core.knowledge_catalog.production_materialization.pipeline import PipelineConfig
class Tests(unittest.TestCase):
    def test_defaults(self):
        c=PipelineConfig().validate()
        self.assertEqual((c.workers,c.max_in_flight,c.artifact_queue_size,c.writer_batch_size),(6,24,32,20))
    def test_bounds(self):
        with self.assertRaises(ValueError):
            PipelineConfig(workers=6,max_in_flight=2).validate()
if __name__=="__main__": unittest.main()
