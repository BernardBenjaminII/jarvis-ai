"""Persistent local-fixture missions. No live target or arbitrary command API."""
import hashlib
import json
import time
import uuid
from core.bounty_lab.engine import Store as LabStore, Denied, scope_check
from .fixture import demo as execute_fixture

CAPABILITY = 'bounty.fixture.http'
MODE = 'owned-loopback-fixture-only'


class Store(LabStore):
    def create(self, include, exclude=(), budget=5, ttl=3600):
        mid = super().create(include, exclude, budget, ttl)
        with self.tx() as db:
            policy = json.loads(self.mission(db, mid)['policy'])
            policy.update(mode=MODE, capability=CAPABILITY)
            raw = json.dumps(policy, sort_keys=True)
            db.execute('UPDATE missions SET policy=?,policy_hash=? WHERE id=?',
                       (raw, hashlib.sha256(raw.encode()).hexdigest(), mid))
            self.event(db, mid, 'fixture_policy', 'Names are synthetic labels, never network destinations')
        return mid

    def validate(self, m, target=None):
        if m['state'] != 'ready' or m['expires'] <= time.time():
            raise Denied('Mission is not ready or has expired')
        if hashlib.sha256(m['policy'].encode()).hexdigest() != m['policy_hash']:
            raise Denied('Policy digest mismatch')
        policy = json.loads(m['policy'])
        if policy.get('mode') != MODE or policy.get('capability') != CAPABILITY:
            raise Denied('Not a local fixture policy')
        if target is not None:
            scope_check(target, policy)

    def queue(self, mid, target, capability=CAPABILITY):
        if capability != CAPABILITY:
            raise Denied('Only the owned HTTP fixture is supported')
        with self.tx() as db:
            m = self.mission(db, mid)
            self.validate(m, target)
            target = scope_check(target, json.loads(m['policy']))
            tid = uuid.uuid4().hex
            result = db.execute('INSERT OR IGNORE INTO tasks VALUES(?,?,?,?,?,NULL)',
                                (tid, mid, target, capability, 'queued'))
            if result.rowcount:
                self.event(db, mid, 'queued', tid)
            return db.execute('SELECT id FROM tasks WHERE mission=? AND target=? AND capability=?',
                              (mid, target, capability)).fetchone()['id']

    def run(self, mid, tid):
        with self.tx() as db:
            m = self.mission(db, mid)
            task = db.execute('SELECT * FROM tasks WHERE id=? AND mission=?', (tid, mid)).fetchone()
            if task is None:
                raise Denied('Task does not belong to mission')
            self.validate(m, task['target'])
            if task['capability'] != CAPABILITY:
                raise Denied('Unsupported capability')
            if task['state'] == 'completed':
                return json.loads(task['evidence'])
            if task['state'] != 'queued' or m['used'] >= m['budget']:
                raise Denied('Task unavailable or budget exhausted; automatic retries disabled')
            digest, target = m['policy_hash'], task['target']
            db.execute("UPDATE tasks SET state='running' WHERE id=?", (tid,))
            db.execute('UPDATE missions SET used=used+1 WHERE id=?', (mid,))
            self.event(db, mid, 'claimed', tid)
        # Commit reservation before external effects; do not hold a DB write lock
        # while running. A crash leaves running + charged, never auto-requeued.
        store = self
        class Control:
            reason = None
            def is_set(self):
                if self.reason:
                    return True
                try:
                    with store.tx() as db:
                        current = store.mission(db, mid)
                        store.validate(current, target)
                        if current['policy_hash'] != digest:
                            raise Denied('Policy changed during execution')
                except Exception:
                    self.reason = 'Mission cancelled, expired, changed, or control check failed'
                return self.reason is not None
        control = Control()
        try:
            result = execute_fixture(cancel=control)
            stopped = control.is_set()
            state = 'cancelled' if stopped else ('completed' if result['passed'] else 'failed')
        except Exception as exc:
            state = 'failed'
            result = {'passed': False, 'error_type': type(exc).__name__}
        evidence = {'task_id': tid, 'target': target, 'policy_sha256': digest,
                    'mode': MODE, 'finding_status': 'not_a_vulnerability',
                    'recorded_at': time.time(), 'result': result}
        with self.tx() as db:
            # Recheck inside the final transaction to order cancellation vs commit.
            current = self.mission(db, mid)
            try:
                self.validate(current, target)
                if current['policy_hash'] != digest:
                    raise Denied('Policy changed')
            except Denied:
                state = 'cancelled'
            evidence['state'] = state
            db.execute('UPDATE tasks SET state=?,evidence=? WHERE id=? AND state=\'running\'',
                       (state, json.dumps(evidence, sort_keys=True), tid))
            self.event(db, mid, 'fixture_' + state, tid)
        return evidence

    def report(self, mid):
        report = super().report(mid)
        report['mode'] = MODE + ' — NOT A BOUNTY SUBMISSION'
        return report
