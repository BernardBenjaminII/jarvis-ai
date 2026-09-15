"""No network, subprocess, dynamic dispatch, or model access in this module.

Policy checks apply only to this laboratory. They do not authorize live testing
or constrain legacy Jarvis tools or users with filesystem access.
"""
from __future__ import annotations
import hashlib
import json
import re
import sqlite3
import time
import uuid
from contextlib import contextmanager
from pathlib import Path

CAPABILITY = "bounty.lab.inspect"

class Denied(ValueError):
    pass


def host(value):
    if not isinstance(value, str) or not value or value != value.strip():
        raise Denied("Expected a canonical hostname, not a URL or command")
    value = value.lower()
    if len(value) > 253 or not all(re.fullmatch(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?", x)
                                   for x in value.split('.')):
        raise Denied("Invalid hostname")
    # A lab-only restriction, not a general-purpose live scope implementation.
    if not value.endswith('.test'):
        raise Denied("R1 accepts only synthetic .test names")
    return value


def pattern(value):
    return '*.' + host(value[2:]) if isinstance(value, str) and value.startswith('*.') else host(value)


def matches(target, rule):
    return target.endswith('.' + rule[2:]) if rule.startswith('*.') else target == rule


def scope_check(target, policy):
    target = host(target)
    if any(matches(target, x) for x in policy['exclude']):
        raise Denied("Target is excluded")
    if not any(matches(target, x) for x in policy['include']):
        raise Denied("Target is outside scope")
    return target


class Store:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.tx() as db:
            db.executescript('''
            CREATE TABLE IF NOT EXISTS missions(
              id TEXT PRIMARY KEY, decision TEXT NOT NULL, state TEXT NOT NULL,
              policy TEXT NOT NULL, policy_hash TEXT NOT NULL, expires REAL NOT NULL,
              budget INTEGER NOT NULL, used INTEGER NOT NULL DEFAULT 0);
            CREATE TABLE IF NOT EXISTS tasks(
              id TEXT PRIMARY KEY, mission TEXT NOT NULL REFERENCES missions(id),
              target TEXT NOT NULL, capability TEXT NOT NULL, state TEXT NOT NULL,
              evidence TEXT, UNIQUE(mission,target,capability));
            CREATE TABLE IF NOT EXISTS events(
              id INTEGER PRIMARY KEY, mission TEXT NOT NULL, at REAL NOT NULL,
              kind TEXT NOT NULL, detail TEXT NOT NULL);
            ''')
        self.path.chmod(0o600)

    @contextmanager
    def tx(self):
        db = sqlite3.connect(self.path, timeout=10)
        db.row_factory = sqlite3.Row
        db.execute('PRAGMA foreign_keys=ON')
        db.execute('BEGIN IMMEDIATE')
        try:
            yield db
            db.commit()
        except BaseException:
            db.rollback()
            raise
        finally:
            db.close()

    def event(self, db, mid, kind, detail):
        db.execute('INSERT INTO events(mission,at,kind,detail) VALUES(?,?,?,?)',
                   (mid, time.time(), kind, detail))

    def mission(self, db, mid):
        row = db.execute('SELECT * FROM missions WHERE id=?', (mid,)).fetchone()
        if row is None:
            raise Denied('Unknown mission')
        return row

    def create(self, include, exclude=(), budget=5, ttl=3600):
        if type(budget) is not int or not 1 <= budget <= 100:
            raise Denied('Budget must be 1..100 lab executions')
        if type(ttl) is not int or not 1 <= ttl <= 86400:
            raise Denied('TTL must be 1..86400 seconds')
        policy = {'include': sorted({pattern(x) for x in include}),
                  'exclude': sorted({pattern(x) for x in exclude}),
                  'mode': 'synthetic-lab-only', 'capability': CAPABILITY}
        if not policy['include']:
            raise Denied('Scope cannot be empty')
        raw = json.dumps(policy, sort_keys=True)
        mid, decision = uuid.uuid4().hex, uuid.uuid4().hex
        with self.tx() as db:
            db.execute('INSERT INTO missions VALUES(?,?,?,?,?,?,?,0)',
                       (mid, decision, 'draft', raw, hashlib.sha256(raw.encode()).hexdigest(),
                        time.time() + ttl, budget))
            self.event(db, mid, 'created', 'Synthetic mission; execution disabled until lab review')
        return mid

    def review(self, mid, reviewer):
        if not isinstance(reviewer, str) or not reviewer.strip():
            raise Denied('Reviewer label is required')
        with self.tx() as db:
            m = self.mission(db, mid)
            if m['state'] != 'draft' or m['expires'] <= time.time():
                raise Denied('Only an unexpired draft may be reviewed')
            db.execute("UPDATE missions SET state='ready' WHERE id=?", (mid,))
            self.event(db, mid, 'lab_review', reviewer.strip())

    def queue(self, mid, target, capability=CAPABILITY):
        if capability != CAPABILITY:
            raise Denied('Live and arbitrary capabilities are disabled')
        with self.tx() as db:
            m = self.mission(db, mid)
            if m['state'] != 'ready' or m['expires'] <= time.time():
                raise Denied('Mission is not ready or has expired')
            target = scope_check(target, json.loads(m['policy']))
            tid = uuid.uuid4().hex
            result = db.execute('INSERT OR IGNORE INTO tasks VALUES(?,?,?,?,?,NULL)',
                                (tid, mid, target, capability, 'queued'))
            if result.rowcount:
                self.event(db, mid, 'queued', tid)
            return db.execute('SELECT id FROM tasks WHERE mission=? AND target=? AND capability=?',
                              (mid, target, capability)).fetchone()['id']

    def cancel(self, mid):
        with self.tx() as db:
            self.mission(db, mid)
            db.execute("UPDATE missions SET state='cancelled' WHERE id=?", (mid,))
            db.execute("UPDATE tasks SET state='cancelled' WHERE mission=? AND state='queued'", (mid,))
            self.event(db, mid, 'cancelled', 'Pending work cancelled')

    def run(self, mid, tid):
        # A single bounded fixture operation runs inside a DB transaction.
        # Crash before commit rolls back evidence AND budget. No external effects.
        with self.tx() as db:
            m = self.mission(db, mid)
            task = db.execute('SELECT * FROM tasks WHERE id=? AND mission=?', (tid, mid)).fetchone()
            if task is None:
                raise Denied('Task does not belong to mission')
            if m['state'] != 'ready' or m['expires'] <= time.time():
                raise Denied('Mission cancelled, unreviewed or expired')
            scope_check(task['target'], json.loads(m['policy']))
            if task['capability'] != CAPABILITY:
                raise Denied('Capability is disabled')
            if task['state'] == 'completed':
                return json.loads(task['evidence'])
            if task['state'] != 'queued' or m['used'] >= m['budget']:
                raise Denied('Task unavailable or mission budget exhausted')
            evidence = {'simulation': True, 'finding_status': 'not_a_vulnerability',
                        'target': task['target'], 'task_id': tid,
                        'policy_sha256': m['policy_hash'], 'recorded_at': time.time(),
                        'observation': 'Synthetic fixture inspected; no network requests were made.'}
            db.execute("UPDATE tasks SET state='completed', evidence=? WHERE id=?",
                       (json.dumps(evidence, sort_keys=True), tid))
            db.execute('UPDATE missions SET used=used+1 WHERE id=?', (mid,))
            self.event(db, mid, 'completed_simulation', tid)
            return evidence

    def report(self, mid):
        with self.tx() as db:
            m = dict(self.mission(db, mid))
            m['policy'] = json.loads(m['policy'])
            tasks = [dict(x) for x in db.execute('SELECT * FROM tasks WHERE mission=? ORDER BY id', (mid,))]
            for task in tasks:
                task['evidence'] = json.loads(task['evidence']) if task['evidence'] else None
            events = [dict(x) for x in db.execute('SELECT * FROM events WHERE mission=? ORDER BY id', (mid,))]
            return {'mode': 'LAB ONLY — NOT A BOUNTY SUBMISSION', 'mission': m,
                    'tasks': tasks, 'events': events}
