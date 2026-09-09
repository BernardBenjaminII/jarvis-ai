from __future__ import annotations

import dataclasses
import inspect
import json
import sqlite3
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any


PROJECT = Path("/media/abdullah/JARVISDATA/Projects/jarvis-ai")
DB = Path("/media/abdullah/JARVIS_RUNTIME_L/knowledge/catalog.sqlite")

if str(PROJECT) not in sys.path:
    sys.path.insert(0, str(PROJECT))


from core.knowledge_catalog import qualified_search as qs
from core.knowledge_catalog import search as search_module


LANE_QUERY = "Edward William Lane Arabic English Lexicon Vol 6"
LANE_ID = 86876

CONTROL_CASES = (
    ("python", "AI assisted Python programming", 11),
    ("cpp", "C++ programming", 4),
    ("effective_c", "effective C programming", 14),
)


def banner(text: str) -> None:
    print()
    print("=" * 78)
    print(text)
    print("=" * 78)


def section(text: str) -> None:
    print()
    print("-" * 78)
    print(text)
    print("-" * 78)


def safe_repr(value: Any, limit: int = 500) -> str:
    try:
        text = repr(value)
    except Exception as exc:
        text = f"<repr failed: {type(exc).__name__}: {exc}>"

    if len(text) > limit:
        return text[:limit] + "...<truncated>"

    return text


def safe_getattr(obj: Any, name: str) -> Any:
    try:
        return getattr(obj, name)
    except Exception as exc:
        return f"<getattr failed: {type(exc).__name__}: {exc}>"


def mapping_view(obj: Any) -> dict[str, Any]:
    if isinstance(obj, Mapping):
        try:
            return dict(obj)
        except Exception:
            return {}

    return {}


def object_dict(obj: Any) -> dict[str, Any]:
    try:
        value = vars(obj)
        if isinstance(value, dict):
            return dict(value)
    except Exception:
        pass

    return {}


def dataclass_view(obj: Any) -> dict[str, Any]:
    try:
        if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
            result = {}
            for field in dataclasses.fields(obj):
                try:
                    result[field.name] = getattr(obj, field.name)
                except Exception as exc:
                    result[field.name] = (
                        f"<field read failed: {type(exc).__name__}: {exc}>"
                    )
            return result
    except Exception:
        pass

    return {}


IDENTITY_NAMES = (
    "id",
    "document_id",
    "runtime_document_id",
    "runtime_id",
    "source_id",
    "catalog_id",
    "doc_id",
    "record_id",
    "rowid",
    "row_id",
    "candidate_id",
    "knowledge_id",
    "object_id",
    "source_document_id",
)


NESTED_NAMES = (
    "metadata",
    "meta",
    "source",
    "document",
    "row",
    "record",
    "payload",
    "candidate",
    "attributes",
    "provenance",
)


TITLE_NAMES = (
    "title",
    "subject",
    "source_path",
    "file_path",
    "path",
    "name",
)


def normalized_scalar(value: Any) -> Any:
    if isinstance(value, bool):
        return value

    if isinstance(value, int):
        return value

    if isinstance(value, float):
        if value.is_integer():
            return int(value)
        return value

    if isinstance(value, str):
        stripped = value.strip()

        if stripped.isdigit():
            try:
                return int(stripped)
            except Exception:
                return stripped

        return stripped

    return value


def direct_named_values(obj: Any) -> dict[str, Any]:
    values: dict[str, Any] = {}

    mapping = mapping_view(obj)
    objdict = object_dict(obj)
    dc = dataclass_view(obj)

    for name in IDENTITY_NAMES + TITLE_NAMES + NESTED_NAMES:
        if name in mapping:
            values[f"mapping.{name}"] = mapping[name]

        if name in objdict:
            values[f"vars.{name}"] = objdict[name]

        if name in dc:
            values[f"dataclass.{name}"] = dc[name]

        try:
            if hasattr(obj, name):
                values[f"attr.{name}"] = getattr(obj, name)
        except Exception:
            pass

    return values


def walk_identity(
    obj: Any,
    *,
    path: str = "root",
    depth: int = 0,
    max_depth: int = 4,
    seen: set[int] | None = None,
) -> list[tuple[str, Any]]:

    if seen is None:
        seen = set()

    results: list[tuple[str, Any]] = []

    if obj is None:
        return results

    if depth > max_depth:
        return results

    if isinstance(obj, (str, bytes, int, float, bool)):
        return results

    oid = id(obj)

    if oid in seen:
        return results

    seen.add(oid)

    mapping = mapping_view(obj)
    objdict = object_dict(obj)
    dc = dataclass_view(obj)

    containers: list[tuple[str, dict[str, Any]]] = []

    if mapping:
        containers.append(("mapping", mapping))

    if objdict:
        containers.append(("vars", objdict))

    if dc:
        containers.append(("dataclass", dc))

    used: set[tuple[str, str]] = set()

    for container_name, container in containers:

        for key, value in container.items():

            key_string = str(key)
            key_lower = key_string.lower()

            marker = (container_name, key_string)

            if marker in used:
                continue

            used.add(marker)

            child_path = f"{path}.{container_name}.{key_string}"

            if (
                key_lower in IDENTITY_NAMES
                or key_lower.endswith("_id")
                or key_lower == "id"
            ):
                results.append((child_path, normalized_scalar(value)))

            if depth < max_depth:
                if (
                    key_lower in NESTED_NAMES
                    or isinstance(value, Mapping)
                    or dataclasses.is_dataclass(value)
                    or hasattr(value, "__dict__")
                ):
                    results.extend(
                        walk_identity(
                            value,
                            path=child_path,
                            depth=depth + 1,
                            max_depth=max_depth,
                            seen=seen,
                        )
                    )

    for name in NESTED_NAMES:
        try:
            if hasattr(obj, name):
                value = getattr(obj, name)

                results.extend(
                    walk_identity(
                        value,
                        path=f"{path}.attr.{name}",
                        depth=depth + 1,
                        max_depth=max_depth,
                        seen=seen,
                    )
                )
        except Exception:
            pass

    return results


def find_identity_values(obj: Any) -> list[tuple[str, Any]]:
    values = walk_identity(obj)

    unique: list[tuple[str, Any]] = []
    seen = set()

    for path, value in values:
        marker = (path, safe_repr(value))

        if marker in seen:
            continue

        seen.add(marker)
        unique.append((path, value))

    return unique


def identity_contains(obj: Any, target_id: int) -> bool:
    target = int(target_id)

    for _, value in find_identity_values(obj):
        value = normalized_scalar(value)

        if value == target:
            return True

    return False


def title_of(obj: Any) -> str | None:
    for name in TITLE_NAMES:

        if isinstance(obj, Mapping):
            value = obj.get(name)

            if value not in (None, ""):
                return str(value)

        try:
            value = getattr(obj, name)

            if value not in (None, ""):
                return str(value)
        except Exception:
            pass

    return None


def print_object_anatomy(label: str, obj: Any) -> None:
    print()
    print(f"{label}")
    print(f"  type       : {type(obj)!r}")
    print(f"  module     : {type(obj).__module__}")
    print(f"  qualname   : {type(obj).__qualname__}")
    print(f"  object id  : {id(obj)}")
    print(f"  repr       : {safe_repr(obj)}")

    try:
        print(f"  dataclass  : {dataclasses.is_dataclass(obj)}")
    except Exception:
        print("  dataclass  : <unknown>")

    try:
        slots = getattr(type(obj), "__slots__", None)
        print(f"  __slots__  : {safe_repr(slots)}")
    except Exception as exc:
        print(f"  __slots__  : <failed: {exc}>")

    objdict = object_dict(obj)

    print(f"  __dict__   : {safe_repr(objdict)}")

    dc = dataclass_view(obj)

    if dc:
        print("  dataclass fields:")

        for key, value in dc.items():
            print(f"    {key:<28} = {safe_repr(value)}")

    named = direct_named_values(obj)

    if named:
        print("  named identity/title fields:")

        for key in sorted(named):
            print(f"    {key:<40} = {safe_repr(named[key])}")

    identities = find_identity_values(obj)

    print(f"  discovered identity values: {len(identities)}")

    for path, value in identities:
        print(f"    {path:<60} = {safe_repr(value)}")


def connect_ro() -> sqlite3.Connection:
    uri = f"file:{DB}?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA query_only = ON")
    return conn


def db_lane_row() -> dict[str, Any] | None:
    conn = connect_ro()

    try:
        tables = {
            row["name"]
            for row in conn.execute(
                "SELECT name FROM sqlite_master "
                "WHERE type='table'"
            )
        }

        candidates = (
            "runtime_documents",
            "documents",
            "catalog",
        )

        for table in candidates:

            if table not in tables:
                continue

            columns = [
                row["name"]
                for row in conn.execute(
                    f"PRAGMA table_info({table})"
                )
            ]

            id_column = None

            for possible in (
                "id",
                "document_id",
                "runtime_document_id",
            ):
                if possible in columns:
                    id_column = possible
                    break

            if id_column is None:
                continue

            row = conn.execute(
                f"SELECT * FROM {table} "
                f"WHERE {id_column} = ? LIMIT 1",
                (LANE_ID,),
            ).fetchone()

            if row is not None:
                result = dict(row)
                result["_table"] = table
                result["_id_column"] = id_column
                return result

    finally:
        conn.close()

    return None


def result_candidate(item: Any) -> Any:
    try:
        candidate = getattr(item, "candidate")
        if candidate is not None:
            return candidate
    except Exception:
        pass

    if isinstance(item, Mapping):
        candidate = item.get("candidate")
        if candidate is not None:
            return candidate

    return item


def inspect_qualification_result(
    query: str,
    target_id: int,
    raw_rows: list[dict[str, Any]],
) -> tuple[Any, Any, list[Any], list[Any]]:

    accepted_rows, result = qs.qualify_rows(
        query,
        raw_rows,
    )

    accepted_items = []

    try:
        accepted_items = list(result.accepted)
    except Exception:
        pass

    rejected_items = []

    try:
        rejected_items = list(result.rejected)
    except Exception:
        pass

    print()
    print("QUALIFICATION RESULT OBJECT")
    print_object_anatomy("result", result)

    print()
    print(f"accepted_rows count : {len(accepted_rows)}")
    print(f"result.accepted     : {len(accepted_items)}")
    print(f"result.rejected     : {len(rejected_items)}")

    matches: list[tuple[str, int, Any, Any]] = []

    for bucket_name, bucket in (
        ("accepted", accepted_items),
        ("rejected", rejected_items),
    ):
        for index, item in enumerate(bucket):

            candidate = result_candidate(item)

            if (
                identity_contains(item, target_id)
                or identity_contains(candidate, target_id)
            ):
                matches.append(
                    (bucket_name, index, item, candidate)
                )

    return result, accepted_rows, accepted_items, rejected_items, matches


def locate_by_title(
    items: list[Any],
    expected_fragments: tuple[str, ...],
) -> list[tuple[int, Any, Any]]:

    found = []

    fragments = tuple(
        fragment.lower()
        for fragment in expected_fragments
    )

    for index, item in enumerate(items):

        candidate = result_candidate(item)
        title = title_of(candidate) or title_of(item) or ""
        lower = title.lower()

        if all(fragment in lower for fragment in fragments):
            found.append((index, item, candidate))

    return found


def inspect_case(
    name: str,
    query: str,
    target_id: int,
    title_fragments: tuple[str, ...],
) -> None:

    banner(f"CASE: {name}")

    print(f"query     : {query}")
    print(f"target ID : {target_id}")

    raw_rows = search_module.search_catalog(
        query,
        db_path=DB,
        limit=100,
    )

    print(f"raw count : {len(raw_rows)}")

    raw_target = None
    raw_rank = None

    for index, row in enumerate(raw_rows, start=1):
        try:
            rid = row.get("id")
        except Exception:
            rid = None

        if normalized_scalar(rid) == target_id:
            raw_target = row
            raw_rank = index
            break

    print(f"raw rank  : {raw_rank}")

    if raw_target is not None:
        print_object_anatomy(
            "RAW TARGET ROW",
            raw_target,
        )
    else:
        print("RAW TARGET ROW: NOT FOUND")

    (
        result,
        accepted_rows,
        accepted_items,
        rejected_items,
        exact_matches,
    ) = inspect_qualification_result(
        query,
        target_id,
        raw_rows,
    )

    print()
    print("EXACT TARGET-ID MATCHES IN QUALIFICATION RESULT")
    print(f"count: {len(exact_matches)}")

    for bucket_name, index, item, candidate in exact_matches:

        print()
        print(
            f"TARGET MATCH bucket={bucket_name} index={index}"
        )

        print_object_anatomy(
            "EVIDENCE / RESULT ITEM",
            item,
        )

        if candidate is not item:
            print_object_anatomy(
                "QUALIFICATION CANDIDATE",
                candidate,
            )

    if not exact_matches:

        print()
        print("NO EXACT ID MATCH DISCOVERED.")
        print("Falling back to deterministic title anatomy.")

        accepted_title = locate_by_title(
            accepted_items,
            title_fragments,
        )

        rejected_title = locate_by_title(
            rejected_items,
            title_fragments,
        )

        print(
            f"title matches accepted : {len(accepted_title)}"
        )
        print(
            f"title matches rejected : {len(rejected_title)}"
        )

        for bucket_name, found in (
            ("accepted", accepted_title),
            ("rejected", rejected_title),
        ):
            for index, item, candidate in found:

                print()
                print(
                    f"TITLE MATCH bucket={bucket_name} "
                    f"index={index}"
                )

                print_object_anatomy(
                    "EVIDENCE / RESULT ITEM",
                    item,
                )

                if candidate is not item:
                    print_object_anatomy(
                        "QUALIFICATION CANDIDATE",
                        candidate,
                    )

    qualified_target_rank = None

    for index, row in enumerate(accepted_rows, start=1):

        if identity_contains(row, target_id):
            qualified_target_rank = index
            break

        try:
            if normalized_scalar(row.get("id")) == target_id:
                qualified_target_rank = index
                break
        except Exception:
            pass

    print()
    print("CASE SUMMARY")
    print(f"raw rank              : {raw_rank}")
    print(f"qualified target rank : {qualified_target_rank}")
    print(f"exact evidence matches: {len(exact_matches)}")


banner("A. MODULE / CLASS ANATOMY")

print(f"qualified module : {qs.__file__}")
print(f"search module    : {search_module.__file__}")

candidate_classes = []

for module in (qs,):

    for name, value in vars(module).items():

        if inspect.isclass(value):

            lname = name.lower()

            if (
                "candidate" in lname
                or "qualification" in lname
                or "evidence" in lname
            ):
                candidate_classes.append(
                    (name, value)
                )

if candidate_classes:
    for name, cls in candidate_classes:

        print()
        print(f"class name : {name}")
        print(f"class      : {cls!r}")
        print(f"module     : {cls.__module__}")

        try:
            print(
                "signature  : "
                f"{inspect.signature(cls)}"
            )
        except Exception as exc:
            print(
                f"signature  : <failed: {exc}>"
            )

        try:
            print(
                f"dataclass  : {dataclasses.is_dataclass(cls)}"
            )
        except Exception:
            pass

        try:
            print(
                f"slots      : {safe_repr(getattr(cls, '__slots__', None))}"
            )
        except Exception:
            pass
else:
    print("No candidate/evidence classes exported directly by qualified_search.")


banner("B. DATABASE LANE IDENTITY")

lane_db = db_lane_row()

if lane_db is None:
    print("Lane ID 86876 not located in inspected document tables.")
else:
    print(f"table     : {lane_db.pop('_table')}")
    print(f"id column : {lane_db.pop('_id_column')}")

    for key, value in lane_db.items():
        print(f"{key:<30}: {safe_repr(value, 1000)}")


banner("C. LANE EXACT SOURCE-ID TRACE")

inspect_case(
    "lane",
    LANE_QUERY,
    LANE_ID,
    (
        "edward",
        "lane",
        "lexicon",
        "vol.6",
    ),
)


banner("D. CONTROL IDENTITY TRACES")

for name, query, target_id in CONTROL_CASES:

    if name == "python":
        fragments = (
            "ai-assisted",
            "python",
        )

    elif name == "cpp":
        fragments = (
            "c++",
            "programming",
        )

    else:
        fragments = (
            "effective c",
            "programming",
        )

    inspect_case(
        name,
        query,
        target_id,
        fragments,
    )


banner("E. DIRECT R1F CANDIDATE TRACE")

original_r1f = qs._gate_repair_should_rescue

events: list[dict[str, Any]] = []


def traced_r1f(query: str, evidence: Any, *, threshold: float):

    candidate = result_candidate(evidence)

    result = original_r1f(
        query,
        evidence,
        threshold=threshold,
    )

    identities_evidence = find_identity_values(evidence)
    identities_candidate = find_identity_values(candidate)

    event = {
        "query": query,
        "result": result,
        "evidence_type": (
            f"{type(evidence).__module__}."
            f"{type(evidence).__qualname__}"
        ),
        "candidate_type": (
            f"{type(candidate).__module__}."
            f"{type(candidate).__qualname__}"
        ),
        "title": title_of(candidate) or title_of(evidence),
        "evidence_identity": identities_evidence,
        "candidate_identity": identities_candidate,
    }

    events.append(event)

    title = event["title"] or ""

    interesting = (
        "Edward.William.Lane" in title
        or "AI-assisted Python" in title
        or "C++ Programming" in title
        or "Effective C" in title
    )

    if interesting:
        print()
        print("R1F INTERCEPT")
        print(f"  query     : {query}")
        print(f"  result    : {result}")
        print(f"  title     : {title}")
        print(f"  evidence  : {event['evidence_type']}")
        print(f"  candidate : {event['candidate_type']}")

        print("  evidence identity:")
        for path, value in identities_evidence:
            print(
                f"    {path:<60} = {safe_repr(value)}"
            )

        print("  candidate identity:")
        for path, value in identities_candidate:
            print(
                f"    {path:<60} = {safe_repr(value)}"
            )

    return result


qs._gate_repair_should_rescue = traced_r1f

try:

    for name, query, target_id in (
        ("lane", LANE_QUERY, LANE_ID),
        *CONTROL_CASES,
    ):

        section(f"LIVE QUALIFIED CALL: {name}")

        rows = qs.search_qualified_catalog(
            query,
            db_path=DB,
            limit=25,
        )

        print(f"returned: {len(rows)}")

finally:
    qs._gate_repair_should_rescue = original_r1f


banner("F. LIVE EVENT IDENTITY SUMMARY")

print(f"total R1F events: {len(events)}")

targets = {
    "lane": LANE_ID,
    "python": 11,
    "cpp": 4,
    "effective_c": 14,
}

for name, target_id in targets.items():

    exact = []

    title_related = []

    for event in events:

        all_values = (
            list(event["evidence_identity"])
            + list(event["candidate_identity"])
        )

        if any(
            normalized_scalar(value) == target_id
            for _, value in all_values
        ):
            exact.append(event)

        title = str(event.get("title") or "").lower()

        if name == "lane":
            if (
                "edward" in title
                and "lane" in title
                and "lexicon" in title
            ):
                title_related.append(event)

        elif name == "python":
            if (
                "ai-assisted" in title
                and "python" in title
            ):
                title_related.append(event)

        elif name == "cpp":
            if "c++ programming" in title:
                title_related.append(event)

        elif name == "effective_c":
            if "effective c" in title:
                title_related.append(event)

    print()
    print(f"{name}")
    print(f"  target ID              : {target_id}")
    print(f"  exact identity events  : {len(exact)}")
    print(f"  title-related events   : {len(title_related)}")

    if exact:
        first = exact[0]

        print("  FIRST EXACT EVENT:")
        print(f"    result : {first['result']}")
        print(f"    title  : {first['title']}")

        print("    evidence identity:")
        for path, value in first["evidence_identity"]:
            print(
                f"      {path:<58} = {safe_repr(value)}"
            )

        print("    candidate identity:")
        for path, value in first["candidate_identity"]:
            print(
                f"      {path:<58} = {safe_repr(value)}"
            )


banner("G. R4-R7 DETERMINATION")

lane_exact = []

for event in events:

    identities = (
        list(event["evidence_identity"])
        + list(event["candidate_identity"])
    )

    if any(
        normalized_scalar(value) == LANE_ID
        for _, value in identities
    ):
        lane_exact.append(event)


if lane_exact:

    print("IDENTITY PATH DISCOVERED: YES")
    print("LANE ID 86876 SURVIVES INTO R1F EVIDENCE: YES")

    print()
    print("Exact Lane identity paths:")

    paths = []

    for event in lane_exact:

        for path, value in (
            list(event["evidence_identity"])
            + list(event["candidate_identity"])
        ):
            if normalized_scalar(value) == LANE_ID:
                paths.append(path)

    for path in sorted(set(paths)):
        print(f"  {path}")

    print()
    print("NEXT ACTION:")
    print(
        "  Use the discovered identity path to build an exact,"
    )
    print(
        "  evidence-bound production identity rescue."
    )

else:

    print("IDENTITY PATH DISCOVERED: NO")
    print("LANE ID 86876 SURVIVES INTO R1F EVIDENCE: NOT PROVEN")

    print()
    print("NEXT ACTION:")
    print(
        "  Do NOT patch production."
    )
    print(
        "  Determine where identity is discarded between raw row"
    )
    print(
        "  materialization and QualificationCandidate construction."
    )


banner("R2-R2A-R4-R7 ANATOMY COMPLETE")

print("R4-R7 is diagnostic only.")
print("No production source or database mutation performed.")
