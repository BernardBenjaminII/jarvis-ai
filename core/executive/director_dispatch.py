from __future__ import annotations

import inspect
from dataclasses import dataclass
from typing import Any, Callable, Iterable


class DirectorDispatchError(RuntimeError):
    """Raised when no canonical ExecutiveDirector callable can be resolved."""


@dataclass(frozen=True, slots=True)
class ResolvedDirectorDispatch:
    method_name: str
    callable: Callable[..., Any]
    signature: str | None
    source_file: str | None
    source_line: int | None
    resolution_basis: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "method_name": self.method_name,
            "signature": self.signature,
            "source_file": self.source_file,
            "source_line": self.source_line,
            "resolution_basis": self.resolution_basis,
        }


DEFAULT_CANDIDATES = (
    "submit",
    "dispatch",
    "direct",
    "route",
    "plan",
    "decide",
    "coordinate",
    "handle",
    "process",
    "run",
    "invoke",
    "execute",
)


def resolve_director_dispatch(
    director: Any,
    *,
    preferred: str | None = None,
    candidates: Iterable[str] = DEFAULT_CANDIDATES,
) -> ResolvedDirectorDispatch:
    if director is None:
        raise DirectorDispatchError("ExecutiveDirector is not available.")

    ordered: list[str] = []

    if preferred:
        ordered.append(preferred)

    for candidate in candidates:
        if candidate not in ordered:
            ordered.append(candidate)

    for method_name in ordered:
        value = getattr(director, method_name, None)

        if not callable(value):
            continue

        try:
            signature = str(inspect.signature(value))
        except Exception:
            signature = None

        try:
            source_file = inspect.getsourcefile(value)
        except Exception:
            source_file = None

        try:
            source_line = inspect.getsourcelines(value)[1]
        except Exception:
            source_line = None

        return ResolvedDirectorDispatch(
            method_name=method_name,
            callable=value,
            signature=signature,
            source_file=source_file,
            source_line=source_line,
            resolution_basis=(
                "preferred_call_graph_result"
                if preferred and method_name == preferred
                else "canonical_candidate_order"
            ),
        )

    public = sorted(
        name
        for name in dir(director)
        if not name.startswith("_")
        and callable(getattr(director, name, None))
    )

    raise DirectorDispatchError(
        "No canonical ExecutiveDirector dispatch method was found. "
        f"Public callable surface: {public}"
    )


def invoke_director(
    director: Any,
    *args: Any,
    preferred: str | None = None,
    **kwargs: Any,
) -> Any:
    resolved = resolve_director_dispatch(
        director,
        preferred=preferred,
    )
    return resolved.callable(*args, **kwargs)
