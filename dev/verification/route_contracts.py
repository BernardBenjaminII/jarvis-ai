
"""Stable route-contract verification without FastAPI private internals."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Iterable, Iterator, Sequence

@dataclass(frozen=True, order=True, slots=True)
class RouteContract:
    method: str
    path: str
    name: str = ""
    def __post_init__(self) -> None:
        method = str(self.method).strip().upper()
        path = str(self.path).strip()
        name = str(self.name).strip()
        if not method:
            raise ValueError("route method is required")
        if not path.startswith("/"):
            raise ValueError("route path must begin with '/'")
        object.__setattr__(self, "method", method)
        object.__setattr__(self, "path", path)
        object.__setattr__(self, "name", name)

def _normalize_methods(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        values = (value,)
    else:
        try:
            values = tuple(value)
        except TypeError:
            values = (value,)
    return tuple(sorted({str(item).strip().upper() for item in values if str(item).strip()}))

def iter_route_contracts(router: Any) -> Iterator[RouteContract]:
    routes = getattr(router, "routes", ())
    if routes is None:
        return
    for route in routes:
        path = getattr(route, "path", None)
        methods = _normalize_methods(getattr(route, "methods", ()))
        name = str(getattr(route, "name", "") or "")
        if isinstance(path, str) and path.startswith("/"):
            for method in methods:
                yield RouteContract(method=method, path=path, name=name)
        nested = getattr(route, "routes", None)
        if nested:
            yield from iter_route_contracts(route)

def collect_route_contracts(*routers: Any) -> tuple[RouteContract, ...]:
    return tuple(sorted({contract for router in routers for contract in iter_route_contracts(router)}))

def has_route(contracts: Iterable[RouteContract], method: str, path: str) -> bool:
    expected_method = str(method).strip().upper()
    expected_path = str(path).strip()
    return any(c.method == expected_method and c.path == expected_path for c in contracts)

def require_routes(routers: Sequence[Any], required: Iterable[tuple[str, str]]) -> tuple[RouteContract, ...]:
    contracts = collect_route_contracts(*routers)
    missing = tuple((str(m).upper(), str(p)) for m, p in required if not has_route(contracts, m, p))
    if missing:
        discovered = ", ".join(f"{c.method} {c.path}" for c in contracts) or "<none>"
        expected = ", ".join(f"{m} {p}" for m, p in missing)
        raise AssertionError(f"Missing canonical route contract(s): {expected}. Discovered: {discovered}")
    return contracts
