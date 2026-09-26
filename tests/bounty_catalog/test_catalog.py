import json
import sqlite3
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock
from core.bounty_catalog.hackerone import Client, DiscoveryError, decode, next_page, page_url, MAX_BYTES
from core.bounty_catalog.store import Catalog, discover


def response(handle='sample', bounty=True, following=None):
    return json.dumps({'data':[{'type':'program','attributes':{'handle':handle,'name':'Example','offers_bounties':bounty}}],
                       'links':{'next':following}}).encode()

class CatalogTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.catalog = Catalog(Path(self.tmp.name)/'catalog.sqlite')

    def test_tri_state(self):
        self.assertEqual([decode(response(bounty=x))[0][0]['reward_status'] for x in (True,False,None)],
                         ['paid','no_bounty','unknown'])
        with self.assertRaises(DiscoveryError):
            decode(response(bounty='true'))

    def test_malformed(self):
        for raw in (b'{}',b'bad',b'x'*(MAX_BYTES+1),response(handle='../evil')):
            with self.subTest(raw=raw[:20]), self.assertRaises(DiscoveryError):
                decode(raw)

    def test_pagination_boundaries(self):
        self.assertEqual(next_page(page_url(2),1),2)
        for url in ('http://api.hackerone.com/v1/hackers/programs',
                    'https://evil.test/v1/hackers/programs', page_url(1),
                    'https://api.hackerone.com@evil.test/v1/hackers/programs',
                    page_url(2)+'&redirect=https://evil.test', page_url(2)+'#fragment'):
            with self.subTest(url=url), self.assertRaises(DiscoveryError):
                next_page(url,1)

    def test_complete_and_paid_filter(self):
        client = MagicMock()
        client.fetch.side_effect = [response('paid',True,page_url(2)),response('vdp',False)]
        result = discover(self.catalog,client,pause=lambda _:None)
        self.assertEqual(result['status'],'complete')
        self.assertEqual(result['pages'],2)
        rows = self.catalog.list(paid_only=True)['programs']
        self.assertEqual([x['handle'] for x in rows],['paid'])
        self.assertFalse(rows[0]['testing_authorized'])
        self.assertEqual(self.catalog.path.stat().st_mode & 0o777,0o600)

    def test_limit(self):
        client = MagicMock()
        client.fetch.return_value = response(following=page_url(2))
        self.assertEqual(discover(self.catalog,client,1)['status'],'limited')
        self.assertEqual(client.fetch.call_count,1)

    def test_partial_error_retained(self):
        client = MagicMock()
        client.fetch.side_effect=[response(following=page_url(2)),DiscoveryError('Rate limited')]
        result=discover(self.catalog,client,pause=lambda _:None)
        self.assertEqual(result['status'],'error')
        self.assertEqual(result['pages'],1)
        self.assertEqual(self.catalog.list()['latest_run']['error'],'Rate limited')

    def test_changed_reward_replaces_latest_not_history(self):
        for value in (True,False):
            self.catalog.save('hackerone-api',time.time(),[(1,response(bounty=value),time.time())],'complete')
        self.assertEqual(self.catalog.list(paid_only=True)['programs'],[])
        with self.catalog.connect() as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM observations').fetchone()[0],2)
            self.assertEqual(db.execute('SELECT COUNT(*) FROM pages').fetchone()[0],2)

    def test_import_separate_and_draft_only(self):
        self.catalog.save('hackerone-import',time.time(),[(1,response(),time.time())],'local_import_unverified')
        self.assertEqual(self.catalog.list()['programs'],[])
        p=self.catalog.proposal('sample','hackerone-import')
        self.assertFalse(p['execution_enabled'])
        self.assertEqual(p['tasks'],[])

    def test_stale_and_missing_latest(self):
        self.catalog.save('hackerone-api',0,[(1,response(),time.time()-90000)],'complete')
        self.catalog.save('hackerone-api',time.time(),[],'error','failed')
        row=self.catalog.list()['programs'][0]
        self.assertTrue(row['stale'])
        self.assertFalse(row['seen_in_latest_run'])

    def test_duplicate_atomic_rollback(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.catalog.save('hackerone-api',0,[(1,response(),1),(2,response(),2)],'complete')
        self.assertIsNone(self.catalog.list()['latest_run'])

    def test_fixed_transport_and_no_secret_output(self):
        with patch('core.bounty_catalog.hackerone.http.client.HTTPSConnection') as conn:
            result=conn.return_value.getresponse.return_value
            result.status=200
            result.getheader.return_value='identity'
            result.read1.side_effect=[response(),b'']
            client=Client('local-user','secret-token')
            self.assertEqual(client.fetch(1),response())
            self.assertEqual(conn.call_args.args[0],'api.hackerone.com')
            call=conn.return_value.request.call_args
            self.assertEqual(call.args[0],'GET')
            self.assertTrue(call.args[1].startswith('/v1/hackers/programs?'))
            result.status=302
            with self.assertRaisesRegex(DiscoveryError,'302'):
                client.fetch(1)
            self.assertEqual(conn.return_value.request.call_count,2)

    def test_auth_and_rate_limit(self):
        with patch('core.bounty_catalog.hackerone.http.client.HTTPSConnection') as conn:
            for status in (401,403,429):
                conn.return_value.getresponse.return_value.status=status
                with self.assertRaises(DiscoveryError) as error:
                    Client('local-user','secret-token').fetch(1)
                self.assertNotIn('secret-token',str(error.exception))

if __name__ == '__main__':
    unittest.main()
