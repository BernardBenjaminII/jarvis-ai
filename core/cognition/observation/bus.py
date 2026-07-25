from __future__ import annotations
from threading import RLock
from .models import Observation, PublicationReceipt
from .enums import ObservationDisposition
from .errors import ObservationSubscriberError

class ExecutiveObservationBus:
    def __init__(self, repository, *, strict_subscribers:bool=False):
        self.repository=repository; self.strict_subscribers=bool(strict_subscribers)
        self._subscribers={}; self._lock=RLock()
    def subscribe(self,name,subscriber):
        name=str(name).strip()
        if not name or not callable(subscriber): raise ValueError("valid subscriber name and callable required")
        with self._lock: self._subscribers[name]=subscriber
    def unsubscribe(self,name):
        with self._lock: return self._subscribers.pop(name,None) is not None
    def publish(self, observation:Observation):
        if not self.repository.append(observation):
            return PublicationReceipt(observation.observation_id,ObservationDisposition.DUPLICATE,0)
        with self._lock: subscribers=tuple(sorted(self._subscribers.items()))
        failures=[]
        for name,subscriber in subscribers:
            try: subscriber(observation)
            except Exception as exc: failures.append(f"{name}: {type(exc).__name__}: {exc}")
        receipt=PublicationReceipt(observation.observation_id,ObservationDisposition.ACCEPTED,len(subscribers),tuple(failures))
        if failures and self.strict_subscribers:
            raise ObservationSubscriberError("; ".join(failures))
        return receipt
