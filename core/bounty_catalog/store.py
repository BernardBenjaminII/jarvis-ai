"""Private local catalog with immutable response snapshots and observation history."""
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import time
import uuid
from .hackerone import decode, next_page, page_url, DiscoveryError

class Catalog:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        fd = os.open(self.path, os.O_CREAT | os.O_RDWR, 0o600)
        os.close(fd)
        self.path.chmod(0o600)
        with self.connect() as db:
            db.executescript('''
            CREATE TABLE IF NOT EXISTS runs(
              id TEXT PRIMARY KEY, source TEXT NOT NULL, started REAL NOT NULL,
              finished REAL NOT NULL, status TEXT NOT NULL, error TEXT);
            CREATE TABLE IF NOT EXISTS pages(
              run TEXT NOT NULL REFERENCES runs(id), number INTEGER NOT NULL,
              url TEXT NOT NULL, observed REAL NOT NULL, sha256 TEXT NOT NULL,
              raw BLOB NOT NULL, PRIMARY KEY(run,number));
            CREATE TABLE IF NOT EXISTS observations(
              run TEXT NOT NULL, page INTEGER NOT NULL, source TEXT NOT NULL,
              handle TEXT NOT NULL, observed REAL NOT NULL, record TEXT NOT NULL,
              PRIMARY KEY(run,handle), FOREIGN KEY(run,page) REFERENCES pages(run,number));
            ''')

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=10)
        db.row_factory = sqlite3.Row
        db.execute('PRAGMA foreign_keys=ON')
        try:
            with db:
                yield db
        finally:
            db.close()

    def save(self, source, started, pages, status, error=None):
        if source not in ('hackerone-api', 'hackerone-import', 'synthetic-demo'):
            raise DiscoveryError('Unknown source')
        run = uuid.uuid4().hex
        # Revalidate every page before opening the write transaction.
        parsed = [(number, raw, at, decode(raw)[0]) for number, raw, at in pages]
        with self.connect() as db:
            db.execute('INSERT INTO runs VALUES(?,?,?,?,?,?)',
                       (run, source, started, time.time(), status, error))
            for number, raw, at, rows in parsed:
                db.execute('INSERT INTO pages VALUES(?,?,?,?,?,?)',
                           (run, number, page_url(number), at, hashlib.sha256(raw).hexdigest(), raw))
                for row in rows:
                    # Duplicates across pages abort the import; never silently drop data.
                    db.execute('INSERT INTO observations VALUES(?,?,?,?,?,?)',
                               (run, number, source, row['handle'], at, json.dumps(row, sort_keys=True)))
        return {'run_id': run, 'source': source, 'status': status, 'pages': len(pages),
                'observations': sum(len(x[3]) for x in parsed), 'error': error,
                'testing_authorized': False}

    def list(self, *, source='hackerone-api', paid_only=False):
        with self.connect() as db:
            records = db.execute('''SELECT o.*, p.url,p.sha256,r.status FROM observations o
              JOIN pages p ON p.run=o.run AND p.number=o.page JOIN runs r ON r.id=o.run
              WHERE o.source=? ORDER BY o.observed DESC,o.rowid DESC''', (source,)).fetchall()
            latest = db.execute('SELECT * FROM runs WHERE source=? ORDER BY finished DESC,rowid DESC LIMIT 1',
                                (source,)).fetchone()
        result, seen = [], set()
        for row in records:
            if row['handle'] in seen:
                continue
            seen.add(row['handle'])
            item = json.loads(row['record'])
            item.pop('policy_text', None)
            if paid_only and item['reward_status'] != 'paid':
                continue
            item.update(source=source, last_seen=row['observed'], source_url=row['url'],
                        source_sha256=row['sha256'], run_id=row['run'], run_status=row['status'],
                        seen_in_latest_run=bool(latest and row['run'] == latest['id']),
                        stale=time.time()-row['observed'] > 86400,
                        review_status='rules_and_eligibility_unreviewed')
            result.append(item)
        result.sort(key=lambda x: (x['reward_status'] != 'paid', x['name'].casefold()))
        return {'latest_run': dict(latest) if latest else None, 'programs': result,
                'testing_authorized': False}

    def proposal(self, handle, source='hackerone-api'):
        candidates = [x for x in self.list(source=source)['programs'] if x['handle'] == handle]
        if not candidates:
            raise DiscoveryError('Program is not in this source catalog')
        return {'state': 'research_draft', 'program': candidates[0], 'execution_enabled': False,
                'required_review': ['Current official policy and full structured scope',
                                    'Exclusions, automation restrictions and request limits',
                                    'Account eligibility and access requirements',
                                    'Asset-specific rewards and permitted test methods'],
                'tasks': [], 'note': 'Listing data does not authorize testing.'}


def discover(catalog, client, max_pages=5, pause=time.sleep):
    if type(max_pages) is not int or not 1 <= max_pages <= 20:
        raise DiscoveryError('max-pages must be 1..20')
    started, pages, status, error = time.time(), [], 'limited', None
    for page in range(1, max_pages + 1):
        try:
            raw = client.fetch(page)
            rows, link = decode(raw)
            following = next_page(link, page)
            pages.append((page, raw, time.time()))
            if following is None:
                status = 'complete'
                break
            if page < max_pages:
                pause(1)
        except DiscoveryError as exc:
            status, error = 'error', str(exc)
            break
    return catalog.save('hackerone-api', started, pages, status, error)
