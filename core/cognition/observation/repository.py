from __future__ import annotations
from threading import RLock
from .models import Observation, ObservationQuery
from .enums import ObservationSeverity
from .errors import ObservationNotFoundError, ObservationRepositoryClosedError

_RANK={x:i for i,x in enumerate(ObservationSeverity)}

class InMemoryObservationRepository:
    def __init__(self):
        self._records={}; self._order=[]; self._closed=False; self._lock=RLock()
    def _open(self):
        if self._closed: raise ObservationRepositoryClosedError("observation repository is closed")
    def append(self, observation:Observation)->bool:
        with self._lock:
            self._open()
            if observation.observation_id in self._records: return False
            self._records[observation.observation_id]=observation; self._order.append(observation.observation_id); return True
    def get(self, observation_id:str)->Observation:
        with self._lock:
            self._open()
            try: return self._records[observation_id]
            except KeyError as e: raise ObservationNotFoundError(observation_id) from e
    def query(self,q:ObservationQuery):
        with self._lock:
            self._open(); items=[self._records[x] for x in self._order]
        def ok(o):
            return ((q.observation_type is None or o.observation_type==q.observation_type)
                and (q.kind is None or o.kind==q.kind)
                and (q.producer is None or o.provenance.producer==q.producer)
                and (q.source is None or o.provenance.source==q.source)
                and (q.mission_id is None or o.mission_id==q.mission_id)
                and (q.correlation_id is None or o.correlation_id==q.correlation_id)
                and (q.minimum_confidence is None or o.confidence>=q.minimum_confidence)
                and (q.minimum_severity is None or _RANK[o.severity]>=_RANK[q.minimum_severity])
                and (q.occurred_from is None or o.occurred_at>=q.occurred_from)
                and (q.occurred_to is None or o.occurred_at<=q.occurred_to))
        out=sorted(filter(ok,items),key=lambda o:(o.occurred_at,o.recorded_at,o.observation_id),reverse=q.newest_first)
        return tuple(out[:q.limit] if q.limit else out)
    def count(self):
        with self._lock: self._open(); return len(self._records)
    def close(self):
        with self._lock: self._closed=True
