"""SITREP with per-source last-good data and nonblocking UI refresh."""
import copy
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from .state_department import StateDepartmentTravelAdvisoryProvider
from .nuclear_sites import NuclearSiteProvider
from .nuclear_events import NrcEventProvider
from .security_news import default_security_providers, group_reports
from .global_security import global_security_providers

COLLECTIONS={'incidents':'incidents','sites':'nuclear_sites','events':'nuclear_events','security_events':'security_events'}

class SitrepService:
    def __init__(self, *, providers=None, cache_ttl_seconds=900.0, monotonic=time.monotonic):
        self._providers=tuple(providers) if providers is not None else (StateDepartmentTravelAdvisoryProvider(),NuclearSiteProvider(),NrcEventProvider(),*default_security_providers(),*global_security_providers())
        self._cache_ttl_seconds=cache_ttl_seconds
        self._monotonic=monotonic
        self._lock=threading.RLock()
        self._collect_lock=threading.Lock()
        self._snapshot=None
        self._expires_at=0.0
        self._last_good={}
        self._refreshing=False

    def _empty(self):
        return dict(operational_state='UNAVAILABLE', generated_at=datetime.now(timezone.utc).isoformat(),
                    incidents=[], nuclear_sites=[], nuclear_events=[], security_events=[],sources=[],errors=[],fixture_count=0)

    def snapshot(self, *, force_refresh=False):
        with self._collect_lock:
            with self._lock:
                if not force_refresh and self._snapshot is not None and self._monotonic()<self._expires_at:
                    return copy.deepcopy(self._snapshot)
            completed={}
            def collect(provider):
                try: return provider.collect(),None
                except Exception as exc: return None,exc
            with ThreadPoolExecutor(max_workers=max(1,min(6,len(self._providers)))) as pool:
                futures={pool.submit(collect,provider):index for index,provider in enumerate(self._providers)}
                for future in as_completed(futures):
                    index=futures[future]
                    result,error=future.result()
                    if error is None: self._last_good[index]=copy.deepcopy(result)
                    completed[index]=(result,error)
                    # Publish each result immediately; slow providers must not hide fast feeds.
                    with self._lock:
                        self._snapshot=self._assemble(completed)
            with self._lock:
                self._snapshot=self._assemble(completed)
                self._expires_at=self._monotonic()+(min(60,self._cache_ttl_seconds) if self._snapshot['errors'] else self._cache_ttl_seconds)
                return copy.deepcopy(self._snapshot)

    def _assemble(self, completed):
        current=self._empty()
        live=0
        pending=0
        for index,provider in enumerate(self._providers):
            provider_id=getattr(provider,'provider_id',type(provider).__name__)
            result,error=completed.get(index,(None,None))
            if index not in completed:
                pending+=1
                result=copy.deepcopy(self._last_good.get(index))
                state='REFRESHING' if result is not None else 'PENDING'
            elif error is None:
                live+=1
                state='LIVE'
            else:
                current['errors'].append(dict(provider_id=provider_id,error_type=type(error).__name__,message=str(error)[:300]))
                result=copy.deepcopy(self._last_good.get(index))
                state='STALE' if result is not None else 'UNAVAILABLE'
            source=dict(provider_id=provider_id,publisher=getattr(provider,'publisher',provider_id),
                        feed_url=getattr(provider,'url',''),retrieved_at=None,state=state,record_count=0)
            if result is not None:
                source['transport_note']=result.get('transport_note','')
                source.update({key:result.get(key,source.get(key)) for key in ('provider_id','publisher','feed_url','retrieved_at')})
                for origin,target in COLLECTIONS.items():
                    rows=copy.deepcopy(list(result.get(origin,())))
                    if state in ('STALE','REFRESHING'):
                        for row in rows: row['operational_state']=state
                    current[target].extend(rows)
                    source['record_count']+=len(rows)
            current['sources'].append(source)
        current['security_events']=group_reports(current['security_events'])
        current['incidents'].sort(key=lambda item:item.get('published_at') or '',reverse=True)
        current['pending_sources']=pending
        current['operational_state']=('PARTIAL' if live else 'LOADING') if pending else 'LIVE' if live and not current['errors'] else 'DEGRADED' if live else 'STALE' if self._last_good else 'UNAVAILABLE'
        return current

    def snapshot_background(self, *, force_refresh=False):
        with self._lock:
            if not self._refreshing and (force_refresh or self._snapshot is None or self._monotonic()>=self._expires_at):
                self._refreshing=True
                threading.Thread(target=self._background_refresh,daemon=True,name='sitrep-refresh').start()
            result=copy.deepcopy(self._snapshot) if self._snapshot is not None else self._assemble({})
            result['refreshing']=self._refreshing
            if self._snapshot is None and self._refreshing: result['operational_state']='LOADING'
            return result

    def _background_refresh(self):
        try: self.snapshot(force_refresh=True)
        finally:
            with self._lock: self._refreshing=False

_service=SitrepService()
def get_sitrep_service(): return _service
