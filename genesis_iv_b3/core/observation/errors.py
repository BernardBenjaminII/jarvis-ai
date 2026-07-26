class ObservationError(Exception): pass
class ObservationValidationError(ObservationError,ValueError): pass
class ObservationSerializationError(ObservationError): pass
class ObservationAdapterError(ObservationError): pass
class ObservationConvergenceError(ObservationError): pass
