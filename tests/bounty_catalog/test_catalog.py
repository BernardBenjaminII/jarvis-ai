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


def test_review_record_preserves_policy_text():
    with tempfile.TemporaryDirectory() as tmp:
        catalog = Catalog(
            Path(tmp) / "catalog.sqlite"
        )

        raw = json.dumps(
            {
                "data": [
                    {
                        "type": "program",
                        "attributes": {
                            "handle": "review-demo",
                            "name": "Review Demo",
                            "offers_bounties": True,
                            "submission_state": "open",
                            "policy": "Synthetic policy text",
                        },
                    }
                ],
                "links": {},
            }
        ).encode()

        catalog.save(
            "hackerone-api",
            time.time(),
            [(1, raw, time.time())],
            "complete",
        )

        record = catalog.review_record(
            "review-demo"
        )

        assert (
            record["policy_text"]
            == "Synthetic policy text"
        )

        assert (
            record["testing_authorized"]
            is False
        )


# === JARVIS R9.9D PROGRAM OPPORTUNITY TESTS ===


def test_r99c_policy_parser_extracts_payout_without_authorizing():
    from core.bounty_catalog.opportunity import (
        parse_policy_signals,
    )

    signals = parse_policy_signals(
        """
        Researchers may use narrowly scoped scanners
        against authorized assets.

        Critical vulnerabilities may receive up to
        $10,000.
        """
    )

    assert signals.payout_max_mention == 10000

    assert (
        signals.automation_policy
        == "explicitly_permitted"
    )

    assert (
        signals.policy_confidence
        == "heuristic_requires_human_policy_review"
    )


def test_r99c_policy_parser_detects_automation_restriction():
    from core.bounty_catalog.opportunity import (
        parse_policy_signals,
    )

    signals = parse_policy_signals(
        """
        Automated scanners, crawlers, scripts,
        and bots are prohibited.
        """
    )

    assert (
        signals.automation_policy
        == "explicitly_prohibited"
    )

    assert signals.automation_restrict_evidence


def test_r99c_policy_parser_mixed_rules_require_review():
    from core.bounty_catalog.opportunity import (
        parse_policy_signals,
    )

    signals = parse_policy_signals(
        """
        Automated scanners are allowed only on the
        documented test host.

        Do not use scanners against production systems.
        """
    )

    assert (
        signals.automation_policy
        == "mixed_context_review_required"
    )

    assert signals.automation_permit_evidence
    assert signals.automation_restrict_evidence


def test_r99c_program_score_never_authorizes_testing():
    from core.bounty_catalog.opportunity import (
        score_program,
    )

    result = score_program(
        {
            "handle": "example-paid",
            "name": "Example Paid",
            "offers_bounties": True,
            "submission_state": "open",
            "state": "public_mode",
            "currency": "usd",
            "open_scope": True,
            "gold_standard_safe_harbor": True,
            "triage_active": True,
            "fast_payments": True,
            "policy": (
                "Narrowly scoped scanners are allowed. "
                "Maximum bounty $15,000."
            ),
        }
    )

    assert result["lane"] == "POLICY_REVIEW"

    assert (
        result["policy_signals"]["automation_policy"]
        == "explicitly_permitted"
    )

    assert result["policy_reward_max_mention"] == 15000
    assert result["policy_review_required"] is True

    assert result["testing_authorized"] is False
    assert result["execution_enabled"] is False
    assert result["automatic_execution_ready"] is False


def test_r99c_restricted_automation_never_enters_auto_lane():
    from core.bounty_catalog.opportunity import (
        score_program,
    )

    result = score_program(
        {
            "handle": "restricted",
            "name": "Restricted Program",
            "offers_bounties": True,
            "submission_state": "open",
            "state": "public_mode",
            "currency": "usd",
            "open_scope": True,
            "gold_standard_safe_harbor": True,
            "triage_active": True,
            "fast_payments": False,
            "policy": (
                "Automated tools and scanners are prohibited. "
                "Maximum bounty $5,000."
            ),
        }
    )

    assert not result["lane"].startswith("AUTO_")

    assert (
        result["policy_signals"]["automation_policy"]
        == "explicitly_prohibited"
    )

    assert result["execution_enabled"] is False


def test_r99c_paused_program_is_skipped():
    from core.bounty_catalog.opportunity import (
        score_program,
    )

    result = score_program(
        {
            "handle": "paused",
            "name": "Paused Program",
            "offers_bounties": True,
            "submission_state": "paused",
            "state": "public_mode",
            "currency": "usd",
            "open_scope": True,
            "policy": (
                "Maximum bounty $25,000."
            ),
        }
    )

    assert result["lane"] == "SKIP"
    assert result["testing_authorized"] is False
    assert result["execution_enabled"] is False


def test_r99c_rank_catalog_is_analysis_only(tmp_path):
    import json
    import time

    from core.bounty_catalog.store import Catalog
    from core.bounty_catalog.opportunity import (
        rank_catalog,
    )

    catalog = Catalog(
        tmp_path / "r99c.sqlite"
    )

    raw = json.dumps(
        {
            "data": [
                {
                    "type": "program",
                    "attributes": {
                        "handle": "alpha",
                        "name": "Alpha",
                        "offers_bounties": True,
                        "submission_state": "open",
                        "state": "public_mode",
                        "currency": "usd",
                        "open_scope": True,
                        "gold_standard_safe_harbor": True,
                        "triage_active": True,
                        "fast_payments": True,
                        "policy": (
                            "Narrowly scoped scanners are allowed "
                            "against authorized assets. "
                            "Maximum bounty $10,000."
                        ),
                    },
                },
                {
                    "type": "program",
                    "attributes": {
                        "handle": "beta",
                        "name": "Beta",
                        "offers_bounties": True,
                        "submission_state": "open",
                        "state": "public_mode",
                        "currency": "usd",
                        "open_scope": False,
                        "gold_standard_safe_harbor": True,
                        "triage_active": True,
                        "fast_payments": False,
                        "policy": (
                            "Automated scanners are prohibited. "
                            "Bounty range $500 - $3,000."
                        ),
                    },
                },
                {
                    "type": "program",
                    "attributes": {
                        "handle": "gamma",
                        "name": "Gamma",
                        "offers_bounties": True,
                        "submission_state": "paused",
                        "state": "public_mode",
                        "currency": "usd",
                        "open_scope": True,
                        "policy": (
                            "Maximum bounty $20,000."
                        ),
                    },
                },
            ],
            "links": {},
        }
    ).encode()

    now = time.time()

    catalog.save(
        "hackerone-api",
        now,
        [
            (
                1,
                raw,
                now,
            )
        ],
        "complete",
    )

    result = rank_catalog(
        catalog
    )

    assert (
        result["schema"]
        == "jarvis-bounty-program-opportunity-r9.9c"
    )

    assert result["program_count"] == 3
    assert result["network_requests"] == 0
    assert result["testing_authorized"] is False
    assert result["execution_enabled"] is False

    assert result["payout_values_authoritative"] is False

    by_handle = {
        item["handle"]: item
        for item in result["opportunities"]
    }

    assert (
        by_handle["alpha"]["lane"]
        == "POLICY_REVIEW"
    )

    assert (
        by_handle["alpha"]["policy_reward_max_mention"]
        == 10000
    )

    assert not (
        by_handle["beta"]["lane"]
        .startswith("AUTO_")
    )

    assert (
        by_handle["gamma"]["lane"]
        == "SKIP"
    )

    for item in result["opportunities"]:
        assert item["testing_authorized"] is False
        assert item["execution_enabled"] is False
        assert item["automatic_execution_ready"] is False
