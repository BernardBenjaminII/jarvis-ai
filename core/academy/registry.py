"""Read-only in-memory registry for EAF-001 static contracts."""

from dataclasses import dataclass
from typing import Generic, Iterable, Iterator, Mapping, TypeVar

from .errors import AcademyContractValidationError

T = TypeVar("T")


@dataclass(frozen=True, slots=True)
class StaticRegistry(Generic[T]):
    _items: Mapping[str, T]

    @classmethod
    def create(cls, entries: Iterable[tuple[str, T]]) -> "StaticRegistry[T]":
        materialized = dict(entries)
        if not materialized:
            raise AcademyContractValidationError("registry cannot be empty")
        return cls(_items=materialized)

    def get(self, identifier: str) -> T:
        try:
            return self._items[identifier]
        except KeyError as exc:
            raise AcademyContractValidationError(
                f"unknown registry identifier: {identifier}"
            ) from exc

    def identifiers(self) -> tuple[str, ...]:
        return tuple(sorted(self._items))

    def __iter__(self) -> Iterator[T]:
        for identifier in self.identifiers():
            yield self._items[identifier]
