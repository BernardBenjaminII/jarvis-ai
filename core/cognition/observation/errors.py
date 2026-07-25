from __future__ import annotations
class ObservationError(Exception): pass
class InvalidObservationError(ObservationError, ValueError): pass
class ObservationNotFoundError(ObservationError, LookupError): pass
class ObservationRepositoryClosedError(ObservationError): pass
class ObservationSubscriberError(ObservationError): pass
