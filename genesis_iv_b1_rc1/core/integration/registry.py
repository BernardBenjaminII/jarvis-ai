from .errors import DuplicateCapabilityError, UnknownCapabilityError
class CapabilityRegistry:
    def __init__(self, capabilities=()):
        self._items={}
        for item in capabilities: self.register(item)
    def register(self, capability):
        if capability.capability_id in self._items: raise DuplicateCapabilityError(capability.capability_id)
        self._items[capability.capability_id]=capability
    def upsert(self, capability): self._items[capability.capability_id]=capability
    def get(self, capability_id):
        try: return self._items[capability_id]
        except KeyError as e: raise UnknownCapabilityError(capability_id) from e
    def all(self): return tuple(self._items[k] for k in sorted(self._items))
    def ids(self): return tuple(sorted(self._items))
    def __contains__(self, capability_id): return capability_id in self._items
