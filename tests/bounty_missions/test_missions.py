import concurrent.futures
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch
from core.bounty_missions.engine import Store, Denied

OK = {'passed': True, 'finding_status': 'not_a_vulnerability'}

class Missions(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.store = Store(Path(self.tmp.name)/'r3.sqlite')
        self.mid = self.store.create(['*.example.test'], ['private.example.test'], budget=1)
        self.store.review(self.mid, 'test')
        self.tid = self.store.queue(self.mid, 'www.example.test')

    def test_real_fixture_persistence_and_replay(self):
        result = self.store.run(self.mid, self.tid)
        self.assertEqual(result['state'], 'completed')
        self.assertEqual(result['result']['fixture_requests'], 1)
        self.assertEqual(result['result']['external_targets_tested'], 0)
        reopened = Store(self.store.path)
        with patch('core.bounty_missions.engine.execute_fixture') as execute:
            self.assertEqual(reopened.run(self.mid, self.tid), result)
            execute.assert_not_called()
        self.assertEqual(reopened.report(self.mid)['mission']['used'], 1)

    def test_scope_and_capability(self):
        for target in ('private.example.test', 'example.test', 'example.com', 'https://www.example.test'):
            with self.assertRaises(Denied):
                self.store.queue(self.mid, target)
        with self.assertRaises(Denied):
            self.store.queue(self.mid, 'www.example.test', 'shell')

    def test_budget_failure_charged(self):
        other = self.store.queue(self.mid, 'other.example.test')
        with patch('core.bounty_missions.engine.execute_fixture', side_effect=RuntimeError('failure')):
            self.assertEqual(self.store.run(self.mid, self.tid)['state'], 'failed')
        with self.assertRaises(Denied):
            self.store.run(self.mid, other)
        with self.assertRaises(Denied):
            self.store.run(self.mid, self.tid)

    def test_cancel_before_claim(self):
        self.store.cancel(self.mid)
        with patch('core.bounty_missions.engine.execute_fixture') as execute:
            with self.assertRaises(Denied):
                self.store.run(self.mid, self.tid)
            execute.assert_not_called()
        self.assertEqual(self.store.report(self.mid)['mission']['used'], 0)

    def test_expiry_before_claim(self):
        with self.store.tx() as db:
            db.execute('UPDATE missions SET expires=0 WHERE id=?', (self.mid,))
        with self.assertRaises(Denied):
            self.store.run(self.mid, self.tid)

    def test_changed_policy(self):
        with self.store.tx() as db:
            db.execute("UPDATE missions SET policy=policy || ' ' WHERE id=?", (self.mid,))
        with self.assertRaises(Denied):
            self.store.run(self.mid, self.tid)

    def test_concurrent_claim_and_cancel(self):
        started, release = threading.Event(), threading.Event()
        def execute(*, cancel):
            started.set()
            self.assertTrue(release.wait(3))
            self.assertTrue(cancel.is_set())
            return {'passed': False}
        with patch('core.bounty_missions.engine.execute_fixture', side_effect=execute) as fixture:
            with concurrent.futures.ThreadPoolExecutor(1) as pool:
                future = pool.submit(self.store.run, self.mid, self.tid)
                try:
                    self.assertTrue(started.wait(3))
                    with self.assertRaises(Denied):
                        Store(self.store.path).run(self.mid, self.tid)
                    self.store.cancel(self.mid)
                finally:
                    release.set()
                self.assertEqual(future.result(timeout=4)['state'], 'cancelled')
            self.assertEqual(fixture.call_count, 1)
        self.assertEqual(self.store.report(self.mid)['mission']['used'], 1)

    def test_expiry_during_execution(self):
        def execute(*, cancel):
            with self.store.tx() as db:
                db.execute('UPDATE missions SET expires=0 WHERE id=?', (self.mid,))
            self.assertTrue(cancel.is_set())
            return OK
        with patch('core.bounty_missions.engine.execute_fixture', side_effect=execute):
            self.assertEqual(self.store.run(self.mid, self.tid)['state'], 'cancelled')

    def test_crash_does_not_requeue_or_refund(self):
        with patch('core.bounty_missions.engine.execute_fixture', side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):
                self.store.run(self.mid, self.tid)
        reopened = Store(self.store.path)
        report = reopened.report(self.mid)
        self.assertEqual(report['mission']['used'], 1)
        self.assertEqual(report['tasks'][0]['state'], 'running')
        with self.assertRaises(Denied):
            reopened.run(self.mid, self.tid)

    def test_wrong_mission_and_unreviewed(self):
        other = self.store.create(['*.example.test'])
        with self.assertRaises(Denied):
            self.store.queue(other, 'www.example.test')
        self.store.review(other, 'test')
        with self.assertRaises(Denied):
            self.store.run(other, self.tid)

if __name__ == '__main__':
    unittest.main()
