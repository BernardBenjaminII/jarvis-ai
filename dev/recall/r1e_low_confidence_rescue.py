from __future__ import annotations

import argparse
import inspect
import json
import math
import sqlite3
import sys
import traceback
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any


def jsonable(value: Any) -> Any:

    if value is None:
        return None

    if isinstance(value, (str, int, float, bool)):
        return value

    if isinstance(value, Path):
        return str(value)

    if is_dataclass(value):
        # Do NOT use dataclasses.asdict() here.
        # asdict() recursively deepcopy()s fields, and production
        # evidence objects may legitimately contain mappingproxy
        # or other read-only/non-pickleable metadata structures.
        #
        # Walk declared dataclass fields directly and feed each
        # value back through jsonable().
        from dataclasses import fields

        return {
            field.name: jsonable(
                getattr(value, field.name)
            )
            for field in fields(value)
        }

    if isinstance(value, dict):
        return {
            str(key): jsonable(val)
            for key, val in value.items()
        }

    if isinstance(value, (list, tuple, set)):
        return [jsonable(item) for item in value]

    if hasattr(value, "value"):
        try:
            return jsonable(value.value)
        except Exception:
            pass

    if hasattr(value, "to_dict"):
        try:
            return jsonable(value.to_dict())
        except Exception:
            pass

    if hasattr(value, "__dict__"):
        try:
            return {
                str(key): jsonable(val)
                for key, val in vars(value).items()
                if not str(key).startswith("_")
            }
        except Exception:
            pass

    return repr(value)


def decision_value(value: Any) -> str:

    if value is None:
        return ""

    if hasattr(value, "value"):
        try:
            return str(value.value)
        except Exception:
            pass

    return str(value)


def row_path(row: dict[str, Any]) -> str:
    return str(
        row.get("file_path")
        or row.get("source_path")
        or ""
    )


def row_title(row: dict[str, Any]) -> str:
    return str(
        row.get("title")
        or row.get("subject")
        or ""
    )


def row_excerpt(row: dict[str, Any]) -> str:
    return str(
        row.get("excerpt")
        or row.get("chunk_text")
        or ""
    )


def candidate_path(candidate: Any) -> str:
    return str(
        getattr(candidate, "source_path", "")
        or ""
    )


def candidate_title(candidate: Any) -> str:
    return str(
        getattr(candidate, "title", "")
        or getattr(candidate, "subject", "")
        or ""
    )


def candidate_excerpt(candidate: Any) -> str:
    return str(
        getattr(candidate, "excerpt", "")
        or ""
    )


def matches_target(
    *,
    title: str,
    path: str,
    excerpt: str,
    terms: tuple[str, ...],
) -> bool:

    haystack = " ".join(
        (
            title,
            path,
            excerpt[:12000],
        )
    ).lower()

    return all(
        term.lower() in haystack
        for term in terms
    )


def score_dict(item: Any) -> dict[str, Any]:

    score = getattr(item, "score", None)

    if score is None:
        return {}

    if hasattr(score, "to_dict"):
        try:
            return jsonable(score.to_dict())
        except Exception:
            pass

    return jsonable(score)


def extract_confidence(candidate: Any) -> Any:

    for name in (
        "confidence",
        "retrieval_confidence",
        "retrieval_score",
        "score",
    ):
        if hasattr(candidate, name):
            value = getattr(candidate, name)
            if isinstance(value, (int, float)):
                return value

    return None


def table_names(db_path: Path) -> list[str]:

    uri = f"file:{db_path}?mode=ro"

    con = sqlite3.connect(
        uri,
        uri=True,
    )

    try:
        rows = con.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type='table'
            ORDER BY name
            """
        ).fetchall()

        return [str(row[0]) for row in rows]

    finally:
        con.close()


def source_of(obj: Any) -> str:

    try:
        return inspect.getsource(obj)
    except Exception as exc:
        return f"<source unavailable: {exc}>"


def signature_of(obj: Any) -> str:

    try:
        return str(inspect.signature(obj))
    except Exception as exc:
        return f"<signature unavailable: {exc}>"


def safe_call_rescue(
    rescue_fn: Any,
    query: str,
    rejected: Any,
    threshold: float,
) -> tuple[Any, Any, str | None]:

    try:
        result = rescue_fn(
            query,
            rejected,
            threshold=threshold,
        )

        if (
            isinstance(result, tuple)
            and len(result) >= 2
        ):
            return (
                bool(result[0]),
                result[1],
                None,
            )

        return (
            bool(result),
            None,
            None,
        )

    except Exception as exc:
        return (
            None,
            None,
            f"{type(exc).__name__}: {exc}",
        )


def evaluate_canary(
    *,
    name: str,
    query: str,
    terms: tuple[str, ...],
    db_path: Path,
    search_catalog: Any,
    search_qualified_catalog: Any,
    qualify_rows: Any,
    engine: Any,
    rescue_fn: Any,
    raw_limit: int = 100,
) -> dict[str, Any]:

    print()
    print("-" * 68)
    print(f"CANARY: {name}")
    print(f"query : {query}")

    raw_rows = list(
        search_catalog(
            query,
            db_path=db_path,
            limit=raw_limit,
        )
    )

    qualified_rows = list(
        search_qualified_catalog(
            query,
            db_path=db_path,
            limit=25,
            engine=engine,
        )
    )

    raw_target = None
    raw_rank = None

    for rank, row in enumerate(raw_rows, 1):

        if matches_target(
            title=row_title(row),
            path=row_path(row),
            excerpt=row_excerpt(row),
            terms=terms,
        ):
            raw_target = row
            raw_rank = rank
            break

    qualified_target = None
    qualified_rank = None

    for rank, row in enumerate(qualified_rows, 1):

        if matches_target(
            title=row_title(row),
            path=row_path(row),
            excerpt=row_excerpt(row),
            terms=terms,
        ):
            qualified_target = row
            qualified_rank = rank
            break

    accepted_rows, qualification_result = qualify_rows(
        query,
        raw_rows,
        engine=engine,
    )

    accepted_rows = list(accepted_rows)

    target_evaluation = None
    target_bucket = None

    for item in qualification_result.accepted:

        candidate = item.candidate

        if matches_target(
            title=candidate_title(candidate),
            path=candidate_path(candidate),
            excerpt=candidate_excerpt(candidate),
            terms=terms,
        ):
            target_evaluation = item
            target_bucket = "accepted"
            break

    if target_evaluation is None:

        for item in qualification_result.rejected:

            candidate = item.candidate

            if matches_target(
                title=candidate_title(candidate),
                path=candidate_path(candidate),
                excerpt=candidate_excerpt(candidate),
                terms=terms,
            ):
                target_evaluation = item
                target_bucket = "rejected"
                break

    rescue = None
    rescue_reason = None
    rescue_error = None

    if (
        target_evaluation is not None
        and target_bucket == "rejected"
    ):
        rescue, rescue_reason, rescue_error = (
            safe_call_rescue(
                rescue_fn,
                query,
                target_evaluation,
                float(qualification_result.threshold),
            )
        )

    evaluation = None

    if target_evaluation is not None:

        candidate = target_evaluation.candidate

        evaluation = {
            "bucket": target_bucket,
            "decision": decision_value(
                target_evaluation.decision
            ),
            "explanation": getattr(
                target_evaluation,
                "explanation",
                None,
            ),
            "candidate": jsonable(candidate),
            "candidate_retrieval_value":
                extract_confidence(candidate),
            "qualification_components":
                score_dict(target_evaluation),
            "rescue": rescue,
            "rescue_reason": rescue_reason,
            "rescue_error": rescue_error,
        }

    result = {
        "name": name,
        "query": query,
        "terms": list(terms),
        "raw_count": len(raw_rows),
        "raw_rank": raw_rank,
        "raw_target": jsonable(raw_target),
        "qualification_accepted_count":
            len(qualification_result.accepted),
        "qualification_rejected_count":
            len(qualification_result.rejected),
        "qualification_threshold":
            qualification_result.threshold,
        "target_evaluation": evaluation,
        "final_qualified_count": len(qualified_rows),
        "final_qualified_rank": qualified_rank,
        "final_qualified_target":
            jsonable(qualified_target),
    }

    print(f"raw rank        : {raw_rank}")
    print(f"raw rows        : {len(raw_rows)}")
    print(
        "engine accepted :",
        len(qualification_result.accepted),
    )
    print(
        "engine rejected :",
        len(qualification_result.rejected),
    )
    print(f"final rank      : {qualified_rank}")
    print(f"final rows      : {len(qualified_rows)}")

    if evaluation:

        print(
            "decision        :",
            evaluation["decision"],
        )

        print(
            "explanation     :",
            evaluation["explanation"],
        )

        print(
            "retrieval value :",
            evaluation["candidate_retrieval_value"],
        )

        print(
            "components      :",
            json.dumps(
                evaluation["qualification_components"],
                indent=2,
                sort_keys=True,
            ),
        )

        print(
            "rescue          :",
            evaluation["rescue"],
        )

        print(
            "rescue reason   :",
            evaluation["rescue_reason"],
        )

        if evaluation["rescue_error"]:
            print(
                "rescue error    :",
                evaluation["rescue_error"],
            )

    else:
        print(
            "decision        : TARGET NOT PRESENT "
            "IN QUALIFICATION INPUT"
        )

    return result


def main() -> int:

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--db",
        required=True,
    )

    parser.add_argument(
        "--report",
        required=True,
    )

    args = parser.parse_args()

    db_path = Path(args.db).resolve()
    report_path = Path(args.report).resolve()

    if not db_path.exists():
        print(
            f"FAIL: DB does not exist: {db_path}",
            file=sys.stderr,
        )
        return 2

    try:

        from core.knowledge_catalog.search import (
            search_catalog,
        )

        from core.knowledge_catalog.qualified_search import (
            search_qualified_catalog,
            qualify_rows,
            _gate_repair_should_rescue,
        )

        from core.retrieval.qualification.evaluator import (
            QualificationEngine,
        )

    except Exception:

        traceback.print_exc()
        return 3

    engine = QualificationEngine()

    print("=== IMPORT CONTRACT ===")
    print(
        "search_catalog:",
        signature_of(search_catalog),
    )
    print(
        "search_qualified_catalog:",
        signature_of(search_qualified_catalog),
    )
    print(
        "qualify_rows:",
        signature_of(qualify_rows),
    )
    print(
        "_gate_repair_should_rescue:",
        signature_of(_gate_repair_should_rescue),
    )
    print(
        "QualificationEngine:",
        signature_of(QualificationEngine),
    )

    print()
    print("=== ACTIVE THRESHOLDS ===")
    print(json.dumps(
        jsonable(engine.thresholds),
        indent=2,
        sort_keys=True,
    ))

    print()
    print("=== READ-ONLY DB TABLE INVENTORY ===")

    tables = table_names(db_path)

    print("table count:", len(tables))

    canaries = [
        {
            "name": "ai_assisted_python",
            "query": "AI assisted Python programming",
            "terms": (
                "python",
                "copilot",
            ),
        },
        {
            "name": "practical_electronics",
            "query": "practical electronics handbook",
            "terms": (
                "practical",
                "electronics",
            ),
        },
        {
            "name": "marx_mathematics",
            "query": "Marx mathematical manuscripts",
            "terms": (
                "marx",
                "mathematical",
            ),
        },
        {
            "name": "effective_c",
            "query": "effective C programming",
            "terms": (
                "effective",
                "c",
            ),
        },
    ]

    results = []

    for spec in canaries:

        results.append(
            evaluate_canary(
                name=spec["name"],
                query=spec["query"],
                terms=spec["terms"],
                db_path=db_path,
                search_catalog=search_catalog,
                search_qualified_catalog=
                    search_qualified_catalog,
                qualify_rows=qualify_rows,
                engine=engine,
                rescue_fn=
                    _gate_repair_should_rescue,
            )
        )

    print()
    print("=" * 68)
    print("R1E DIFFERENTIAL")

    python_case = next(
        item
        for item in results
        if item["name"] == "ai_assisted_python"
    )

    comparison_cases = [
        item
        for item in results
        if item["name"] != "ai_assisted_python"
    ]

    def evaluation(case):
        return case.get("target_evaluation") or {}

    py_eval = evaluation(python_case)

    rescued_controls = [
        item
        for item in comparison_cases
        if evaluation(item).get("rescue") is True
    ]

    accepted_controls = [
        item
        for item in comparison_cases
        if item.get("final_qualified_rank") is not None
    ]

    differential = {
        "python_raw_rank":
            python_case.get("raw_rank"),
        "python_final_rank":
            python_case.get("final_qualified_rank"),
        "python_decision":
            py_eval.get("decision"),
        "python_explanation":
            py_eval.get("explanation"),
        "python_components":
            py_eval.get("qualification_components"),
        "python_rescue":
            py_eval.get("rescue"),
        "python_rescue_reason":
            py_eval.get("rescue_reason"),
        "rescued_controls": [
            item["name"]
            for item in rescued_controls
        ],
        "accepted_controls": [
            item["name"]
            for item in accepted_controls
        ],
    }

    diagnosis = "UNCLASSIFIED"

    if python_case["raw_rank"] is None:

        diagnosis = (
            "PYTHON_NOT_PRESENT_IN_RAW_RETRIEVAL"
        )

    elif py_eval.get("bucket") != "rejected":

        if python_case["final_qualified_rank"] is not None:
            diagnosis = (
                "PYTHON_ACCEPTED_NO_RESCUE_FAILURE"
            )
        else:
            diagnosis = (
                "POST_ENGINE_OUTPUT_LOSS"
            )

    elif (
        py_eval.get("decision")
        == "rejected_low_confidence"
        and py_eval.get("rescue") is False
    ):

        diagnosis = (
            "LOW_CONFIDENCE_RELEVANT_EVIDENCE_"
            "RESCUE_GAP"
        )

    elif (
        py_eval.get("decision")
        == "rejected_low_confidence"
        and py_eval.get("rescue") is True
        and python_case["final_qualified_rank"] is None
    ):

        diagnosis = (
            "RESCUE_APPROVED_BUT_OUTPUT_LOST"
        )

    elif (
        py_eval.get("decision")
        == "rejected_low_confidence"
        and python_case["final_qualified_rank"] is not None
    ):

        diagnosis = (
            "LOW_CONFIDENCE_RESCUE_WORKING"
        )

    report = {
        "certification":
            "GENESIS_RECALL_R1E",
        "purpose":
            "Low-confidence relevant-evidence rescue certification",
        "production_db":
            str(db_path),
        "active_thresholds":
            jsonable(engine.thresholds),
        "table_count":
            len(tables),
        "canaries":
            results,
        "differential":
            differential,
        "diagnosis":
            diagnosis,
        "source": {
            "rescue_signature":
                signature_of(
                    _gate_repair_should_rescue
                ),
            "rescue_function":
                source_of(
                    _gate_repair_should_rescue
                ),
        },
    }

    report_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    report_path.write_text(
        json.dumps(
            report,
            indent=2,
            sort_keys=True,
            default=str,
        )
        + "\n",
        encoding="utf-8",
    )

    print()
    print("DIAGNOSIS:", diagnosis)

    print()
    print("Python boundary:")
    print(
        "  raw rank       :",
        python_case.get("raw_rank"),
    )
    print(
        "  engine decision:",
        py_eval.get("decision"),
    )
    print(
        "  explanation    :",
        py_eval.get("explanation"),
    )
    print(
        "  rescue         :",
        py_eval.get("rescue"),
    )
    print(
        "  rescue reason  :",
        py_eval.get("rescue_reason"),
    )
    print(
        "  final rank     :",
        python_case.get(
            "final_qualified_rank"
        ),
    )

    print()
    print("Control rescue outcomes:")

    for case in comparison_cases:

        ev = evaluation(case)

        print(
            f"  {case['name']:<24} "
            f"raw={str(case.get('raw_rank')):<4} "
            f"decision={str(ev.get('decision')):<28} "
            f"rescue={str(ev.get('rescue')):<5} "
            f"reason={str(ev.get('rescue_reason')):<24} "
            f"final={case.get('final_qualified_rank')}"
        )

    print()
    print("JSON report:", report_path)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
