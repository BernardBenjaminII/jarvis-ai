from __future__ import annotations

import dataclasses
import inspect
import pprint
import sqlite3
import sys
import traceback
from collections.abc import Mapping
from pathlib import Path
from types import MappingProxyType
from typing import Any


PROJECT = Path(
    "/media/abdullah/JARVISDATA/Projects/jarvis-ai"
)

DB = Path(
    "/media/abdullah/JARVIS_RUNTIME_L/knowledge/catalog.sqlite"
)

LANE_RUNTIME_ID = 86876

LANE_QUERY = (
    "Edward William Lane Arabic English Lexicon Vol 6"
)


def heading(text: str) -> None:
    print()
    print("=" * 76)
    print(text)
    print("=" * 76)


def subheading(text: str) -> None:
    print()
    print("-" * 76)
    print(text)
    print("-" * 76)


def safe_repr(value: Any, limit: int = 12000) -> str:
    try:
        text = repr(value)
    except Exception as exc:
        text = (
            f"<repr failed: {type(exc).__name__}: {exc}>"
        )

    if len(text) > limit:
        return text[:limit] + "\n... <repr truncated>"

    return text


def print_type(label: str, value: Any) -> None:
    print(f"{label:<28}: {type(value)!r}")


def dump_mapping(
    mapping: Mapping[Any, Any],
    *,
    indent: str = "  ",
) -> None:
    for key, value in mapping.items():
        print(
            f"{indent}{key!r}: "
            f"type={type(value)!r} "
            f"value={safe_repr(value, 3000)}"
        )


def dump_object(
    label: str,
    value: Any,
    *,
    depth: int = 0,
    max_depth: int = 3,
) -> None:
    prefix = "  " * depth

    print()
    print(
        f"{prefix}{label}: "
        f"type={type(value)!r}"
    )

    print(
        f"{prefix}repr: "
        f"{safe_repr(value, 5000)}"
    )

    if value is None:
        return

    if depth >= max_depth:
        print(
            f"{prefix}<maximum introspection depth reached>"
        )
        return

    # --------------------------------------------------------
    # Dataclass anatomy
    # --------------------------------------------------------

    try:
        is_dc = dataclasses.is_dataclass(value)
    except Exception:
        is_dc = False

    print(
        f"{prefix}is_dataclass: {is_dc}"
    )

    if is_dc:
        try:
            fields = dataclasses.fields(value)
            print(
                f"{prefix}dataclass fields:"
            )

            for field in fields:
                try:
                    child = getattr(value, field.name)
                except Exception as exc:
                    print(
                        f"{prefix}  {field.name}: "
                        f"<getattr failed: {exc}>"
                    )
                    continue

                print(
                    f"{prefix}  {field.name}: "
                    f"type={type(child)!r} "
                    f"value={safe_repr(child, 3000)}"
                )

        except Exception as exc:
            print(
                f"{prefix}dataclass field inspection failed: "
                f"{type(exc).__name__}: {exc}"
            )

    # --------------------------------------------------------
    # __dict__
    # --------------------------------------------------------

    try:
        obj_dict = vars(value)
    except Exception as exc:
        print(
            f"{prefix}__dict__: unavailable "
            f"({type(exc).__name__}: {exc})"
        )
        obj_dict = None

    if obj_dict is not None:
        print(
            f"{prefix}__dict__ keys: "
            f"{list(obj_dict.keys())}"
        )

        for key, child in obj_dict.items():
            print(
                f"{prefix}  {key}: "
                f"type={type(child)!r} "
                f"value={safe_repr(child, 3000)}"
            )

    # --------------------------------------------------------
    # Mapping
    # --------------------------------------------------------

    if isinstance(value, Mapping):
        print(
            f"{prefix}mapping keys: "
            f"{list(value.keys())}"
        )

        for key, child in value.items():
            print(
                f"{prefix}  mapping[{key!r}]: "
                f"type={type(child)!r} "
                f"value={safe_repr(child, 3000)}"
            )

    # --------------------------------------------------------
    # Sequence
    # --------------------------------------------------------

    if isinstance(value, (list, tuple)):
        print(
            f"{prefix}sequence length: {len(value)}"
        )

        for index, child in enumerate(value):
            print(
                f"{prefix}  [{index}]: "
                f"type={type(child)!r} "
                f"value={safe_repr(child, 3000)}"
            )

    # --------------------------------------------------------
    # Public attribute inventory
    # --------------------------------------------------------

    try:
        names = [
            name
            for name in dir(value)
            if not name.startswith("__")
        ]

        print(
            f"{prefix}public attributes/methods:"
        )

        for name in names:
            try:
                child = getattr(value, name)
            except Exception as exc:
                print(
                    f"{prefix}  {name}: "
                    f"<getattr failed: {exc}>"
                )
                continue

            if callable(child):
                try:
                    sig = inspect.signature(child)
                except Exception:
                    sig = "<signature unavailable>"

                print(
                    f"{prefix}  {name}: "
                    f"CALLABLE {sig}"
                )
            else:
                print(
                    f"{prefix}  {name}: "
                    f"type={type(child)!r} "
                    f"value={safe_repr(child, 3000)}"
                )

    except Exception as exc:
        print(
            f"{prefix}dir() failed: "
            f"{type(exc).__name__}: {exc}"
        )


def source_or_failure(obj: Any) -> str:
    try:
        return inspect.getsource(obj)
    except Exception as exc:
        return (
            "<source unavailable: "
            f"{type(exc).__name__}: {exc}>"
        )


def signature_or_failure(obj: Any) -> str:
    try:
        return str(inspect.signature(obj))
    except Exception as exc:
        return (
            "<signature unavailable: "
            f"{type(exc).__name__}: {exc}>"
        )


def find_runtime_schema(
    conn: sqlite3.Connection,
) -> dict[str, str | None]:
    rows = conn.execute(
        "PRAGMA table_info(runtime_documents)"
    ).fetchall()

    columns = {
        str(row["name"])
        for row in rows
    }

    def choose(*names: str) -> str | None:
        for name in names:
            if name in columns:
                return name
        return None

    return {
        "id": choose(
            "id",
            "runtime_document_id",
            "document_id",
        ),
        "title": choose(
            "title",
            "document_title",
            "name",
        ),
        "path": choose(
            "file_path",
            "source_path",
            "path",
        ),
        "text": choose(
            "text",
            "content",
            "body",
            "document_text",
        ),
        "source_type": choose(
            "source_type",
            "type",
            "document_type",
        ),
    }


def load_lane_row(
    conn: sqlite3.Connection,
) -> dict[str, Any]:
    row = conn.execute(
        """
        SELECT *
        FROM runtime_documents
        WHERE id = ?
        LIMIT 1
        """,
        (LANE_RUNTIME_ID,),
    ).fetchone()

    if row is None:
        raise RuntimeError(
            f"Lane runtime id {LANE_RUNTIME_ID} not found"
        )

    return dict(row)


def candidate_from_runtime_row(
    row: dict[str, Any],
    schema: dict[str, str | None],
) -> dict[str, Any]:
    """
    Construct the simplest production-compatible row possible.

    This intentionally preserves the original runtime_documents
    values and adds only the aliases needed to expose identity
    semantics to qualify_rows().
    """

    candidate = dict(row)

    id_col = schema["id"]
    title_col = schema["title"]
    path_col = schema["path"]
    text_col = schema["text"]
    type_col = schema["source_type"]

    runtime_id = (
        row.get(id_col)
        if id_col
        else LANE_RUNTIME_ID
    )

    title = (
        row.get(title_col)
        if title_col
        else None
    )

    path = (
        row.get(path_col)
        if path_col
        else None
    )

    text = (
        row.get(text_col)
        if text_col
        else None
    )

    source_type = (
        row.get(type_col)
        if type_col
        else None
    )

    # Preserve common production aliases.
    candidate.setdefault(
        "runtime_document_id",
        runtime_id,
    )

    candidate.setdefault(
        "document_id",
        runtime_id,
    )

    candidate.setdefault(
        "id",
        runtime_id,
    )

    candidate.setdefault(
        "title",
        title,
    )

    candidate.setdefault(
        "subject",
        title,
    )

    candidate.setdefault(
        "file_path",
        path,
    )

    candidate.setdefault(
        "source_path",
        path,
    )

    candidate.setdefault(
        "path",
        path,
    )

    if text is not None:
        candidate.setdefault(
            "text",
            text,
        )

        candidate.setdefault(
            "content",
            text,
        )

    if source_type is not None:
        candidate.setdefault(
            "source_type",
            source_type,
        )

    return candidate


def main() -> int:
    heading(
        "GENESIS RECALL R2-R2A-R2 "
        "— QUALIFICATIONRESULT OBJECT ANATOMY"
    )

    # ========================================================
    # 1. IMPORT PRODUCTION OBJECTS
    # ========================================================

    heading("1. PRODUCTION IMPORTS")

    from core.knowledge_catalog.qualified_search import (
        qualify_rows,
    )

    import core.knowledge_catalog.qualified_search as qs

    from core.retrieval.qualification.evaluator import (
        QualificationEngine,
    )

    import core.retrieval.qualification.evaluator as ev

    print(
        "qualify_rows signature       :",
        signature_or_failure(qualify_rows),
    )

    print(
        "QualificationEngine signature:",
        signature_or_failure(QualificationEngine),
    )

    # ========================================================
    # 2. READ-ONLY DATABASE
    # ========================================================

    heading("2. READ-ONLY DATABASE CONTRACT")

    uri = f"file:{DB}?mode=ro"

    conn = sqlite3.connect(
        uri,
        uri=True,
    )

    conn.row_factory = sqlite3.Row

    conn.execute(
        "PRAGMA query_only = ON"
    )

    query_only = conn.execute(
        "PRAGMA query_only"
    ).fetchone()[0]

    integrity = conn.execute(
        "PRAGMA integrity_check"
    ).fetchone()[0]

    print("query_only :", query_only)
    print("integrity  :", integrity)

    if int(query_only) != 1:
        raise RuntimeError(
            "query_only not active"
        )

    if str(integrity).lower() != "ok":
        raise RuntimeError(
            f"database integrity failure: {integrity}"
        )

    # ========================================================
    # 3. RUNTIME SCHEMA
    # ========================================================

    heading("3. runtime_documents SCHEMA")

    schema = find_runtime_schema(conn)

    for key, value in schema.items():
        print(f"{key:<12}: {value}")

    if schema["id"] is None:
        raise RuntimeError(
            "runtime_documents ID column not found"
        )

    # ========================================================
    # 4. LOAD EXACT LANE DOCUMENT
    # ========================================================

    heading("4. EXACT LANE RUNTIME DOCUMENT")

    lane_row = load_lane_row(conn)

    print("runtime id :", LANE_RUNTIME_ID)

    for key, value in lane_row.items():
        rendered = safe_repr(value, 2500)
        print(
            f"{key:<28}: "
            f"type={type(value)!r} "
            f"value={rendered}"
        )

    # ========================================================
    # 5. MATERIALIZE CANDIDATE
    # ========================================================

    heading("5. QUALIFICATION INPUT CANDIDATE")

    candidate = candidate_from_runtime_row(
        lane_row,
        schema,
    )

    print("query:")
    print(LANE_QUERY)

    print()
    print("candidate keys:")
    print(sorted(candidate.keys()))

    print()
    print("candidate:")

    for key, value in candidate.items():
        print(
            f"{key:<28}: "
            f"type={type(value)!r} "
            f"value={safe_repr(value, 2500)}"
        )

    # ========================================================
    # 6. QUALIFY EXACTLY ONE CANDIDATE
    # ========================================================

    heading("6. EXACT qualify_rows() RETURN ANATOMY")

    engine = QualificationEngine()

    result = qualify_rows(
        LANE_QUERY,
        [candidate],
        engine=engine,
    )

    print_type(
        "qualify_rows return",
        result,
    )

    print(
        "qualify_rows repr:",
        safe_repr(result, 12000),
    )

    dump_object(
        "qualify_rows return object",
        result,
    )

    if not isinstance(result, tuple):
        print()
        print(
            "CRITICAL OBSERVATION: qualify_rows() "
            "did not return a tuple."
        )

        accepted_rows = None
        qualification = result
    else:
        print()
        print(
            "tuple length:",
            len(result),
        )

        for index, item in enumerate(result):
            dump_object(
                f"tuple[{index}]",
                item,
            )

        if len(result) >= 2:
            accepted_rows = result[0]
            qualification = result[1]
        elif len(result) == 1:
            accepted_rows = result[0]
            qualification = None
        else:
            accepted_rows = None
            qualification = None

    # ========================================================
    # 7. ACCEPTED ROWS ANATOMY
    # ========================================================

    heading("7. ACCEPTED ROWS ANATOMY")

    dump_object(
        "accepted_rows",
        accepted_rows,
    )

    # ========================================================
    # 8. QUALIFICATION OBJECT ANATOMY
    # ========================================================

    heading("8. QUALIFICATION OBJECT ANATOMY")

    dump_object(
        "qualification",
        qualification,
    )

    # ========================================================
    # 9. RECURSIVE FIELD PROBE
    # ========================================================

    heading("9. QUALIFICATION FIELD-BY-FIELD PROBE")

    if qualification is None:
        print("qualification is None")

    else:
        field_names: list[str] = []

        if dataclasses.is_dataclass(qualification):
            try:
                field_names.extend(
                    field.name
                    for field in dataclasses.fields(
                        qualification
                    )
                )
            except Exception:
                pass

        try:
            field_names.extend(
                vars(qualification).keys()
            )
        except Exception:
            pass

        if isinstance(qualification, Mapping):
            field_names.extend(
                str(key)
                for key in qualification.keys()
            )

        # Include likely semantic locations even if they are
        # properties rather than dataclass fields.
        field_names.extend(
            [
                "accepted",
                "rejected",
                "evidence",
                "evidences",
                "results",
                "evaluations",
                "candidates",
                "scores",
                "decision",
                "explanation",
                "score",
                "threshold",
            ]
        )

        seen: set[str] = set()

        for field_name in field_names:
            if field_name in seen:
                continue

            seen.add(field_name)

            print()
            print(
                f"FIELD: {field_name}"
            )

            try:
                if isinstance(
                    qualification,
                    Mapping,
                ) and field_name in qualification:
                    child = qualification[field_name]
                else:
                    child = getattr(
                        qualification,
                        field_name,
                    )
            except Exception as exc:
                print(
                    "  unavailable:",
                    f"{type(exc).__name__}: {exc}",
                )
                continue

            dump_object(
                field_name,
                child,
                depth=1,
                max_depth=2,
            )

    # ========================================================
    # 10. CLASS DEFINITIONS
    # ========================================================

    heading("10. QUALIFICATION CLASS SOURCE")

    if qualification is not None:
        print(
            source_or_failure(
                type(qualification)
            )
        )
    else:
        print(
            "No qualification instance available."
        )

    # ========================================================
    # 11. qualify_rows SOURCE
    # ========================================================

    heading("11. qualify_rows() PRODUCTION SOURCE")

    print(
        source_or_failure(
            qualify_rows
        )
    )

    # ========================================================
    # 12. QUALIFICATION ENGINE SOURCE MAP
    # ========================================================

    heading("12. QualificationEngine SOURCE")

    print(
        source_or_failure(
            QualificationEngine
        )
    )

    # ========================================================
    # 13. MODULE CLASS INVENTORY
    # ========================================================

    heading("13. QUALIFICATION MODULE CLASS INVENTORY")

    for name, obj in inspect.getmembers(
        ev,
        inspect.isclass,
    ):
        if obj.__module__ != ev.__name__:
            continue

        print()
        print(
            f"{name}: "
            f"{signature_or_failure(obj)}"
        )

        try:
            fields = dataclasses.fields(obj)

            print(
                "  dataclass fields:",
                [
                    field.name
                    for field in fields
                ],
            )
        except Exception:
            pass

    # ========================================================
    # 14. QUALIFIED_SEARCH MODULE FUNCTIONS
    # ========================================================

    heading("14. qualified_search FUNCTION INVENTORY")

    for name, obj in inspect.getmembers(
        qs,
        inspect.isfunction,
    ):
        if obj.__module__ != qs.__name__:
            continue

        print(
            f"{name:<40} "
            f"{signature_or_failure(obj)}"
        )

    # ========================================================
    # 15. SEARCH FOR EVIDENCE-LIKE OBJECTS
    # ========================================================

    heading("15. EVIDENCE-LIKE OBJECT DISCOVERY")

    roots = [
        ("return", result),
        ("accepted_rows", accepted_rows),
        ("qualification", qualification),
    ]

    visited: set[int] = set()

    def walk(
        path: str,
        obj: Any,
        depth: int = 0,
    ) -> None:
        if obj is None:
            return

        if depth > 5:
            return

        # Avoid recursion through immutable scalar objects.
        if isinstance(
            obj,
            (
                str,
                bytes,
                int,
                float,
                bool,
            ),
        ):
            return

        oid = id(obj)

        if oid in visited:
            return

        visited.add(oid)

        cls_name = type(obj).__name__.lower()

        interesting = any(
            token in cls_name
            for token in (
                "evidence",
                "qualification",
                "score",
                "candidate",
                "result",
            )
        )

        if interesting:
            print()
            print(
                f"DISCOVERED: {path}"
            )
            print(
                f"  type : {type(obj)!r}"
            )
            print(
                f"  repr : {safe_repr(obj, 5000)}"
            )

        if dataclasses.is_dataclass(obj):
            try:
                for field in dataclasses.fields(obj):
                    try:
                        child = getattr(
                            obj,
                            field.name,
                        )
                    except Exception:
                        continue

                    walk(
                        f"{path}.{field.name}",
                        child,
                        depth + 1,
                    )
            except Exception:
                pass

        if isinstance(obj, Mapping):
            for key, child in obj.items():
                walk(
                    f"{path}[{key!r}]",
                    child,
                    depth + 1,
                )

        elif isinstance(obj, (list, tuple)):
            for index, child in enumerate(obj):
                walk(
                    f"{path}[{index}]",
                    child,
                    depth + 1,
                )

        else:
            try:
                attrs = vars(obj)
            except Exception:
                attrs = {}

            for key, child in attrs.items():
                walk(
                    f"{path}.{key}",
                    child,
                    depth + 1,
                )

    for path, root in roots:
        walk(path, root)

    # ========================================================
    # 16. DIRECT ENGINE METHOD INVENTORY
    # ========================================================

    heading("16. QualificationEngine METHOD INVENTORY")

    for name, method in inspect.getmembers(
        engine,
        predicate=callable,
    ):
        if name.startswith("__"):
            continue

        try:
            sig = inspect.signature(method)
        except Exception:
            sig = "<signature unavailable>"

        print(
            f"{name:<36}: {sig}"
        )

    # ========================================================
    # 17. CONCLUSION
    # ========================================================

    heading("17. R2-R2A-R2 INTROSPECTION RESULT")

    print(
        "Lane runtime document       : FOUND"
    )

    print(
        "Lane candidate constructed  : YES"
    )

    print(
        "qualify_rows invoked        : YES"
    )

    print(
        "return object exposed       : YES"
    )

    print(
        "qualification anatomy dumped: YES"
    )

    print(
        "production source changes   : 0"
    )

    print(
        "production DB writes        : 0"
    )

    print()
    print(
        "R2-R2A-R2 INTROSPECTION: PASS"
    )

    conn.close()

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception:
        print()
        print(
            "R2-R2A-R2 INTROSPECTION: FAIL"
        )
        traceback.print_exc()
        raise SystemExit(1)
