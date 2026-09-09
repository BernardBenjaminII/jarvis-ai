"""SITREP aggregation with honest live/stale/unavailable states."""
import copy, threading, time
from datetime import datetime, timezone
from .state_department import StateDepartmentTravelAdvisoryProvider

class SitrepService:
    def __init__(self, *, providers=None, cache_ttl_seconds=900.0, monotonic=time.monotonic):
        self._providers=providers or (StateDepartmentTravelAdvisoryProvider(),); self._cache_ttl_seconds=cache_ttl_seconds; self._monotonic=monotonic; self._lock=threading.RLock(); self._snapshot=None; self._expires_at=0.0
    def snapshot(self, *, force_refresh=False):
        with self._lock:
            if not force_refresh and self._snapshot is not None and self._monotonic() < self._expires_at: return copy.deepcopy(self._snapshot)
            incidents=[]; sources=[]; errors=[]
            for provider in self._providers:
                try:
                    result=provider.collect(); records=list(result.get("incidents",())); incidents.extend(records)
                    sources.append({"provider_id":result["provider_id"],"publisher":result["publisher"],"feed_url":result["feed_url"],"retrieved_at":result["retrieved_at"],"state":"LIVE","record_count":len(records)})
                except Exception as exc:
                    errors.append({"provider_id":getattr(provider,"provider_id",type(provider).__name__),"error_type":type(exc).__name__,"message":str(exc)[:300]})
            if sources:
                incidents.sort(key=lambda item:item.get("published_at") or "", reverse=True)
                snapshot={"operational_state":"LIVE" if not errors else "DEGRADED","generated_at":datetime.now(timezone.utc).isoformat(),"incidents":incidents,"sources":sources,"errors":errors,"fixture_count":0}
                self._snapshot=snapshot; self._expires_at=self._monotonic()+self._cache_ttl_seconds; return copy.deepcopy(snapshot)
            if self._snapshot is not None:
                stale=copy.deepcopy(self._snapshot); stale["operational_state"]="STALE"; stale["errors"]=errors
                for incident in stale["incidents"]: incident["operational_state"]="STALE"
                for source in stale["sources"]: source["state"]="STALE"
                return stale
            return {"operational_state":"UNAVAILABLE","generated_at":datetime.now(timezone.utc).isoformat(),"incidents":[],"sources":[],"errors":errors,"fixture_count":0}

_service=SitrepService()
def get_sitrep_service(): return _service
