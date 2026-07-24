"""Deterministic bounded working memory for Genesis VI-A2."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Dict, Iterable, Iterator, Tuple

from .enums import MemoryEntryKind
from .errors import (
    DuplicateMemoryEntryError,
    WorkingMemoryCapacityError,
)
from .models import MemoryEntry


@dataclass(frozen=True, slots=True)
class WorkingMemorySnapshot:
    """Immutable snapshot of executive working memory."""

    capacity: int
    entries: Tuple[MemoryEntry, ...]

    def __post_init__(self) -> None:
        if self.capacity < 1:
            raise ValueError("capacity must be at least 1")
        if len(self.entries) > self.capacity:
            raise ValueError("entries exceed snapshot capacity")

    @property
    def size(self) -> int:
        """Return the number of entries in the snapshot."""

        return len(self.entries)

    @property
    def remaining_capacity(self) -> int:
        """Return the number of available entry slots."""

        return self.capacity - self.size

    def get(self, entry_id: str) -> MemoryEntry | None:
        """Return an entry by identifier."""

        for entry in self.entries:
            if entry.entry_id == entry_id:
                return entry
        return None

    def by_kind(self, kind: MemoryEntryKind) -> Tuple[MemoryEntry, ...]:
        """Return entries matching a memory-entry kind."""

        return tuple(entry for entry in self.entries if entry.kind is kind)


class WorkingMemory:
    """Bounded deterministic executive working memory.

    Entries are indexed by ``entry_id``. When the memory is full, a newly
    admitted entry may evict the weakest existing entry if and only if its
    retention key is strictly stronger.

    Retention ordering is deterministic and uses:

    1. importance;
    2. confidence;
    3. creation timestamp;
    4. entry identifier.

    Higher values are retained. Entry identifiers provide the final stable
    tie-breaker.
    """

    def __init__(self, capacity: int = 32) -> None:
        if capacity < 1:
            raise ValueError("capacity must be at least 1")

        self._capacity = capacity
        self._entries: Dict[str, MemoryEntry] = {}

    @property
    def capacity(self) -> int:
        """Return maximum number of retained entries."""

        return self._capacity

    @property
    def size(self) -> int:
        """Return number of retained entries."""

        return len(self._entries)

    @property
    def remaining_capacity(self) -> int:
        """Return number of available entry slots."""

        return self.capacity - self.size

    @property
    def is_full(self) -> bool:
        """Return whether the memory has reached capacity."""

        return self.size >= self.capacity

    def __len__(self) -> int:
        return self.size

    def __contains__(self, entry_id: object) -> bool:
        return isinstance(entry_id, str) and entry_id in self._entries

    def __iter__(self) -> Iterator[MemoryEntry]:
        return iter(self.entries())

    @staticmethod
    def _retention_key(entry: MemoryEntry) -> tuple[float, float, str, str]:
        return (
            entry.importance,
            entry.confidence,
            entry.created_at.isoformat(),
            entry.entry_id,
        )

    def _weakest_entry(self) -> MemoryEntry:
        if not self._entries:
            raise WorkingMemoryCapacityError(
                "cannot select an eviction candidate from empty memory"
            )
        return min(self._entries.values(), key=self._retention_key)

    def admit(self, entry: MemoryEntry) -> MemoryEntry | None:
        """Admit an entry and return an evicted entry when applicable.

        Duplicate identifiers are rejected. If memory is full and the new entry
        is not strictly stronger than the weakest retained entry, admission is
        rejected with ``WorkingMemoryCapacityError``.
        """

        if entry.entry_id in self._entries:
            raise DuplicateMemoryEntryError(
                f"working-memory entry already exists: {entry.entry_id}"
            )

        if not self.is_full:
            self._entries[entry.entry_id] = entry
            return None

        weakest = self._weakest_entry()
        if self._retention_key(entry) <= self._retention_key(weakest):
            raise WorkingMemoryCapacityError(
                "working memory is full and the new entry does not outrank "
                f"eviction candidate {weakest.entry_id}"
            )

        del self._entries[weakest.entry_id]
        self._entries[entry.entry_id] = entry
        return weakest

    def admit_many(
        self,
        entries: Iterable[MemoryEntry],
    ) -> Tuple[MemoryEntry, ...]:
        """Admit entries in input order and return all evictions."""

        evicted = []
        for entry in entries:
            removed = self.admit(entry)
            if removed is not None:
                evicted.append(removed)
        return tuple(evicted)

    def get(self, entry_id: str) -> MemoryEntry | None:
        """Return an entry by identifier."""

        return self._entries.get(entry_id)

    def require(self, entry_id: str) -> MemoryEntry:
        """Return an entry or raise ``KeyError``."""

        try:
            return self._entries[entry_id]
        except KeyError as exc:
            raise KeyError(f"working-memory entry not found: {entry_id}") from exc

    def entries(self) -> Tuple[MemoryEntry, ...]:
        """Return entries ordered from strongest to weakest."""

        return tuple(
            sorted(
                self._entries.values(),
                key=self._retention_key,
                reverse=True,
            )
        )

    def by_kind(self, kind: MemoryEntryKind) -> Tuple[MemoryEntry, ...]:
        """Return entries of a given kind in retention order."""

        return tuple(entry for entry in self.entries() if entry.kind is kind)

    def replace(self, entry: MemoryEntry) -> MemoryEntry:
        """Replace an existing entry and return the previous value."""

        previous = self.require(entry.entry_id)
        self._entries[entry.entry_id] = entry
        return previous

    def update(
        self,
        entry_id: str,
        *,
        content: str | None = None,
        importance: float | None = None,
        confidence: float | None = None,
        source: str | None = None,
        metadata: dict | None = None,
    ) -> MemoryEntry:
        """Replace selected fields while preserving identity and creation time."""

        current = self.require(entry_id)
        updated = replace(
            current,
            content=current.content if content is None else content,
            importance=current.importance if importance is None else importance,
            confidence=current.confidence if confidence is None else confidence,
            source=current.source if source is None else source,
            metadata=current.metadata if metadata is None else metadata,
        )
        self._entries[entry_id] = updated
        return updated

    def remove(self, entry_id: str) -> MemoryEntry:
        """Remove and return an entry."""

        try:
            return self._entries.pop(entry_id)
        except KeyError as exc:
            raise KeyError(f"working-memory entry not found: {entry_id}") from exc

    def discard(self, entry_id: str) -> MemoryEntry | None:
        """Remove and return an entry when present."""

        return self._entries.pop(entry_id, None)

    def clear(self) -> Tuple[MemoryEntry, ...]:
        """Clear memory and return the prior deterministic contents."""

        previous = self.entries()
        self._entries.clear()
        return previous

    def snapshot(self) -> WorkingMemorySnapshot:
        """Return an immutable deterministic snapshot."""

        return WorkingMemorySnapshot(
            capacity=self.capacity,
            entries=self.entries(),
        )
