from core.bounty_agent.scoring_r61 import analyze_http_evidence, analyze_http_evidence_only

def test_hash_does_not_fake_403():
    e={"target":"a.staging.airtable.com","scope":{"source_digest":"aaa403bbb","scope_sha256":"ccc403ddd"},"result":{"records":[]}}
    o=analyze_http_evidence_only(e)
    assert "Access-controlled endpoint returned 401/403" not in o["reasons"]
    assert o["evidence_summary"]["status_codes"] == []

def test_real_403_counts():
    e={"target":"dl.staging.airtable.com","result":{"records":[{"url":"https://dl.staging.airtable.com","status_code":403,"webserver":"CloudFront"}]}}
    o=analyze_http_evidence_only(e)
    assert "Access-controlled endpoint returned 401/403" in o["reasons"]
    assert o["evidence_summary"]["status_codes"] == [403]

def test_api_redirect():
    e={"target":"content.staging.airtable.com","result":{"records":[{"url":"https://content.staging.airtable.com","status_code":302,"location":"https://staging.airtable.com/api"}]}}
    o=analyze_http_evidence_only(e)
    assert "API-like application surface identified" in o["reasons"]

def test_no_record_low():
    e={"target":"dead.staging.airtable.com","result":{"records":[]}}
    o=analyze_http_evidence_only(e)
    assert o["score"] < 20
