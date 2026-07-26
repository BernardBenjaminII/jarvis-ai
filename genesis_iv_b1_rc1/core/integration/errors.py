class IntegrationFabricError(Exception): pass
class DuplicateCapabilityError(IntegrationFabricError): pass
class UnknownCapabilityError(IntegrationFabricError): pass
class InvalidIntegrationDefinitionError(IntegrationFabricError): pass
