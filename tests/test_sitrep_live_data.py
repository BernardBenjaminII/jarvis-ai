from datetime import datetime, timezone
from core.sitrep.service import SitrepService
from core.sitrep.state_department import StateDepartmentTravelAdvisoryProvider
from core.sitrep.nuclear_sites import NuclearSiteProvider
from core.sitrep.nuclear_events import NrcEventProvider
from pathlib import Path

PAYLOAD={"features":[{"attributes":{"OBJECTID":3,"NAME":"Afghanistan","LEVEL_":4,"URL":"https://travel.state.gov/content/travel/en/traveladvisories/traveladvisories/afghanistan-advisory.html","ADVDATE":1771616650000,"ISO_3":"AFG","GlobalID":"1fa5012a-afee-40e8-93ac-daf32dc905a9","EditDate":1771616652751,"AD_OD_Status":None,"AD_OD_Text":None,"AD_OD_Date":None},"centroid":{"x":67.7,"y":33.9}},{"attributes":{"OBJECTID":1,"NAME":None,"LEVEL_":None,"URL":None}}]}

def test_provider_normalizes_arcgis_record():
    incident=StateDepartmentTravelAdvisoryProvider(clock=lambda:datetime(2026,9,9,tzinfo=timezone.utc)).parse(PAYLOAD)["incidents"][0]
    assert incident["region"]=="Afghanistan" and incident["advisory_level"]==4 and incident["severity"]=="critical"
    assert incident["location"]=={"latitude":33.9,"longitude":67.7} and incident["source"]["authority"]=="primary"
def test_provider_rejects_untrusted_advisory_urls():
    payload={"features":[{"attributes":{"NAME":"Test","LEVEL_":4,"URL":"https://example.com/fake"}}]}
    try: StateDepartmentTravelAdvisoryProvider().parse(payload)
    except ValueError as exc: assert "no valid advisory" in str(exc)
    else: raise AssertionError("untrusted URL was accepted")
class Provider:
    provider_id="test"
    def __init__(self): self.fail=False
    def collect(self):
        if self.fail: raise TimeoutError("offline")
        return {"provider_id":"test","publisher":"Authority","feed_url":"https://example.test/feed","retrieved_at":"2026-09-09T00:00:00+00:00","incidents":[{"id":"1","published_at":None,"operational_state":"LIVE"}]}
def test_service_returns_live_without_fixtures():
    result=SitrepService(providers=(Provider(),),cache_ttl_seconds=0).snapshot(); assert result["operational_state"]=="LIVE" and result["fixture_count"]==0
def test_service_retains_last_good_snapshot_as_stale():
    provider=Provider(); service=SitrepService(providers=(provider,),cache_ttl_seconds=0); service.snapshot(); provider.fail=True
    result=service.snapshot(force_refresh=True); assert result["operational_state"]=="STALE" and result["incidents"][0]["operational_state"]=="STALE"
def test_service_never_fabricates_when_unavailable():
    provider=Provider(); provider.fail=True; result=SitrepService(providers=(provider,)).snapshot(); assert result["operational_state"]=="UNAVAILABLE" and result["incidents"]==[] and result["fixture_count"]==0

def test_nuclear_site_provider_normalizes_public_reference_location():
    payload={"elements":[{"type":"way","id":42,"center":{"lat":50.1,"lon":8.6},"tags":{"name":"Example Nuclear Station","power":"plant","operator":"Example Utility"}}]}
    result=NuclearSiteProvider(clock=lambda:datetime(2026,9,9,tzinfo=timezone.utc)).parse(payload)
    site=result["sites"][0]
    assert site["kind"]=="nuclear_site" and site["location"]=={"latitude":50.1,"longitude":8.6}
    assert site["source"]["authority"]=="public_reference"

def test_nrc_provider_preserves_regulator_notice_classification():
    text="Event Desc|En No|Site Name|Licensee Name|State Cd|Notification Dt|Event Dt|Emergency Class|Event Text|\nPower Reactor|57999|Example Station|Example Utility|VA|09/09/2026|09/09/2026|Notification of Unusual Event|Official regulator narrative.|"
    event=NrcEventProvider(clock=lambda:datetime(2026,9,9,tzinfo=timezone.utc)).parse(text)["events"][0]
    assert event["id"]=="nrc-57999" and event["classification"]=="REGULATOR NOTICE"
    assert event["source"]["authority"]=="primary" and event["severity"]=="watch"

def test_service_keeps_nuclear_collections_separate_from_travel_incidents():
    class NuclearProvider:
        provider_id="nuclear-test"
        def collect(self):
            return {"provider_id":self.provider_id,"publisher":"Authority","feed_url":"https://example.test","retrieved_at":"2026-09-09T00:00:00+00:00","sites":[{"id":"s1"}],"events":[{"id":"e1"}]}
    result=SitrepService(providers=(NuclearProvider(),),cache_ttl_seconds=0).snapshot()
    assert result["incidents"]==[] and len(result["nuclear_sites"])==1 and len(result["nuclear_events"])==1

def test_sitrep_frontend_uses_workspace_root_not_inner_map():
    script=(Path(__file__).resolve().parents[1]/"core/src/static/mission_control/sitrep_workspace.js").read_text()
    assert "root=host;" in script
    assert 'root=host.querySelector(".sitrep")' not in script

def test_sitrep_frontend_has_priority_sort_clustering_and_layer_contract():
    script=(Path(__file__).resolve().parents[1]/"core/src/static/mission_control/sitrep_workspace.js").read_text()
    assert "Number(b.advisory_level)-Number(a.advisory_level)" in script
    assert "groups=new Map()" in script
    assert "Nuclear sites + notices" in script
    assert "source.authority" in script
