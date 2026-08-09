"""Genesis VIII-A0-3 canonical Government serialization API."""

from .canonical import canonical_bytes, canonical_fingerprint, canonical_json
from .codec import GovernmentCodec, GovernmentSerializable
from .envelope import (
    GOVERNMENT_SCHEMA_VERSION,
    SUPPORTED_GOVERNMENT_SCHEMA_VERSIONS,
    GovernmentEnvelope,
)
from .errors import (
    GovernmentFingerprintError,
    GovernmentPayloadError,
    GovernmentSerializationError,
    UnsupportedGovernmentSchemaError,
)

__all__ = [
    "GOVERNMENT_SCHEMA_VERSION",
    "GovernmentCodec",
    "GovernmentEnvelope",
    "GovernmentFingerprintError",
    "GovernmentPayloadError",
    "GovernmentSerializable",
    "GovernmentSerializationError",
    "SUPPORTED_GOVERNMENT_SCHEMA_VERSIONS",
    "UnsupportedGovernmentSchemaError",
    "canonical_bytes",
    "canonical_fingerprint",
    "canonical_json",
]
