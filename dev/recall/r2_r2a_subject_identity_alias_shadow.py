from __future__ import annotations

import json
import re
import sqlite3
import sys
import time
import unicodedata

from dataclasses import asdict, is_dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any, Iterable, Mapping


PROJECT = Path(
    "/media/abdullah/JARVISDATA/Projects/jarvis-ai"
)

DB = Path(
    "/media/abdullah/JARVIS_RUNTIME_L/knowledge/catalog.sqlite"
)

OUTDIR = PROJECT / "artifacts/genesis_recall"

REPORT = (
    OUTDIR
    / "r2_r2a_subject_identity_alias_shadow.json"
)

TSV = (
    OUTDIR
    / "r2_r2a_subject_identity_alias_shadow.tsv"
)


# ------------------------------------------------------------
# IMPORT PRODUCTION COMPONENTS
# ------------------------------------------------------------

from core.knowledge_catalog.search import (
    search_catalog,
)

from core.knowledge_catalog.qualified_search import (
    qualify_rows,
)

from core.retrieval.qualification.evaluator import (
    QualificationEngine,
)


# ------------------------------------------------------------
# SERIALIZATION
# ------------------------------------------------------------

def jsonable(value: Any) -> Any:
    if value is None:
        return None

    if isinstance(
        value,
        (
            str,
            int,
            float,
            bool,
        ),
    ):
        return value

    if isinstance(value, Path):
        return str(value)

    if isinstance(value, MappingProxyType):
        return {
            str(k): jsonable(v)
            for k, v in dict(value).items()
        }

    if isinstance(value, Mapping):
        return {
            str(k): jsonable(v)
            for k, v in value.items()
        }

    if isinstance(value, (list, tuple, set)):
        return [
            jsonable(v)
            for v in value
        ]

    if is_dataclass(value):
        result = {}

        for field in value.__dataclass_fields__.values():
            try:
                result[field.name] = jsonable(
                    getattr(value, field.name)
                )
            except Exception:
                result[field.name] = repr(
                    getattr(value, field.name, None)
                )

        return result

    if hasattr(value, "__dict__"):
        return {
            str(k): jsonable(v)
            for k, v in vars(value).items()
            if not str(k).startswith("_")
        }

    return repr(value)


# ------------------------------------------------------------
# GENERIC ACCESS
# ------------------------------------------------------------

def get_value(
    obj: Any,
    name: str,
    default: Any = None,
) -> Any:
    if obj is None:
        return default

    if isinstance(obj, Mapping):
        return obj.get(name, default)

    return getattr(obj, name, default)


def runtime_id(row: Any) -> int | None:
    for key in (
        "runtime_id",
        "runtime_document_id",
        "document_id",
        "id",
    ):
        value = get_value(row, key)

        if value is None:
            continue

        try:
            return int(value)
        except Exception:
            continue

    return None


def title_of(row: Any) -> str:
    for key in (
        "title",
        "subject",
        "name",
        "filename",
        "file_name",
    ):
        value = get_value(row, key)

        if value:
            return str(value)

    return ""


# ------------------------------------------------------------
# CONSERVATIVE IDENTITY NORMALIZATION
# ------------------------------------------------------------

APOSTROPHES = {
    "\u2018",
    "\u2019",
    "\u02bc",
    "\u0060",
    "\u00b4",
}


def identity_normalize(text: str) -> str:
    """
    Conservative document-identity normalization.

    This is NOT production code.

    Purpose:
      - filename punctuation normalization
      - extension removal
      - apostrophe normalization
      - possessive normalization
      - separator normalization
      - volume-number normalization

    No stemming.
    No fuzzy edit distance.
    No synonym expansion.
    """

    text = unicodedata.normalize(
        "NFKC",
        str(text or ""),
    )

    for char in APOSTROPHES:
        text = text.replace(char, "'")

    text = text.casefold()

    # Filename extensions.
    text = re.sub(
        r"\.(pdf|txt|htm|html|epub|docx?|rtf|odt)\s*$",
        " ",
        text,
    )

    # English possessive.
    text = re.sub(
        r"\b([a-z0-9]+)'s\b",
        r"\1",
        text,
    )

    # Vol.6 / Vol 6 / volume.6
    text = re.sub(
        r"\bvol(?:ume)?\.?\s*(\d+)\b",
        r"vol \1",
        text,
    )

    # Punctuation and filename separators become spaces.
    text = re.sub(
        r"[^a-z0-9]+",
        " ",
        text,
    )

    text = re.sub(
        r"\s+",
        " ",
        text,
    ).strip()

    return text


def identity_tokens(text: str) -> tuple[str, ...]:
    return tuple(
        token
        for token in identity_normalize(text).split()
        if token
    )


def ordered_subsequence(
    query_tokens: Iterable[str],
    candidate_tokens: Iterable[str],
) -> bool:
    q = tuple(query_tokens)
    c = tuple(candidate_tokens)

    if not q:
        return False

    pos = 0

    for token in c:
        if token == q[pos]:
            pos += 1

            if pos == len(q):
                return True

    return False


def token_coverage(
    query_tokens: Iterable[str],
    candidate_tokens: Iterable[str],
) -> float:
    q = tuple(query_tokens)
    c = set(candidate_tokens)

    if not q:
        return 0.0

    matched = sum(
        1
        for token in q
        if token in c
    )

    return matched / len(q)


def identity_alias_analysis(
    query: str,
    title: str,
) -> dict[str, Any]:
    qnorm = identity_normalize(query)
    tnorm = identity_normalize(title)

    qt = identity_tokens(query)
    tt = identity_tokens(title)

    coverage = token_coverage(qt, tt)

    ordered = ordered_subsequence(
        qt,
        tt,
    )

    exact = (
        bool(qnorm)
        and qnorm == tnorm
    )

    phrase = (
        bool(qnorm)
        and qnorm in tnorm
    )

    # Conservative deterministic alias.
    #
    # Extra title tokens are allowed, e.g. "(Dictionary)".
    # Every query token must still be represented and retain order.
    alias = (
        len(qt) >= 3
        and coverage == 1.0
        and ordered
    )

    return {
        "query_normalized": qnorm,
        "title_normalized": tnorm,
        "query_tokens": list(qt),
        "title_tokens": list(tt),
        "coverage": coverage,
        "ordered": ordered,
        "exact": exact,
        "phrase": phrase,
        "identity_alias": alias,
    }


# ------------------------------------------------------------
# QUALIFICATION ANALYSIS
# ------------------------------------------------------------

def qualification_for(
    query: str,
    row: Mapping[str, Any],
    engine: QualificationEngine,
) -> tuple[Any, Any]:
    accepted, result = qualify_rows(
        query,
        [row],
        engine=engine,
    )

    evidence = None

    for name in (
        "evidence",
        "evaluations",
        "candidates",
        "items",
    ):
        value = get_value(result, name)

        if value:
            try:
                evidence = list(value)[0]
                break
            except Exception:
                pass

    if evidence is None:
        evidence = result

    return accepted, evidence


def evidence_fields(evidence: Any) -> dict[str, Any]:
    candidate = get_value(
        evidence,
        "candidate",
    )

    score = get_value(
        evidence,
        "score",
    )

    decision = get_value(
        evidence,
        "decision",
    )

    explanation = get_value(
        evidence,
        "explanation",
    )

    if hasattr(decision, "value"):
        decision = decision.value

    return {
        "decision": (
            str(decision)
            if decision is not None
            else None
        ),
        "explanation": explanation,
        "candidate_subject": get_value(
            candidate,
            "subject",
        ),
        "candidate_title": get_value(
            candidate,
            "title",
        ),
        "candidate_source_path": get_value(
            candidate,
            "source_path",
        ),
        "retrieval_score": get_value(
            candidate,
            "retrieval_score",
        ),
        "score_lexical": get_value(
            score,
            "lexical",
        ),
        "score_phrase": get_value(
            score,
            "phrase",
        ),
        "score_entity": get_value(
            score,
            "entity",
        ),
        "score_subject": get_value(
            score,
            "subject",
        ),
        "score_provenance": get_value(
            score,
            "provenance",
        ),
        "score_confidence": get_value(
            score,
            "confidence",
        ),
        "score_final": get_value(
            score,
            "final",
        ),
    }


# ------------------------------------------------------------
# SHADOW IDENTITY QUALIFICATION
# ------------------------------------------------------------

def shadow_identity_qualification(
    *,
    alias: dict[str, Any],
    fields: dict[str, Any],
    accepted_baseline: bool,
    deterministic_identity_hit: bool,
    accept_threshold: float,
) -> dict[str, Any]:
    """
    Test an identity-aware qualification rule.

    Important:
      Identity does NOT automatically mean "answer the question".

    It may only repair a subject mismatch when:
      1. retrieval itself deterministically identified the document;
      2. normalized title identity is strong;
      3. overall qualification score already clears normal acceptance;
      4. provenance is strong;
      5. lexical relevance is non-trivial.

    This deliberately preserves the existing global acceptance floor.
    """

    try:
        final = float(
            fields.get("score_final") or 0.0
        )
    except Exception:
        final = 0.0

    try:
        lexical = float(
            fields.get("score_lexical") or 0.0
        )
    except Exception:
        lexical = 0.0

    try:
        provenance = float(
            fields.get("score_provenance") or 0.0
        )
    except Exception:
        provenance = 0.0

    decision = str(
        fields.get("decision") or ""
    )

    if accepted_baseline:
        return {
            "accepted": True,
            "reason": "already_accepted",
        }

    if not deterministic_identity_hit:
        return {
            "accepted": False,
            "reason": "no_deterministic_identity_hit",
        }

    if not alias.get("identity_alias"):
        return {
            "accepted": False,
            "reason": "identity_alias_not_proven",
        }

    if "subject" not in decision.lower():
        return {
            "accepted": False,
            "reason": "not_subject_mismatch",
        }

    if final < float(accept_threshold):
        return {
            "accepted": False,
            "reason": "final_below_normal_accept_threshold",
        }

    if lexical < 0.20:
        return {
            "accepted": False,
            "reason": "lexical_below_normal_floor",
        }

    if provenance < 0.50:
        return {
            "accepted": False,
            "reason": "weak_provenance",
        }

    return {
        "accepted": True,
        "reason": "deterministic_identity_alias_subject_repair",
    }


# ------------------------------------------------------------
# CANARIES
# ------------------------------------------------------------

CANARIES = (
    {
        "name": "list_sora",
        "query": "List Sora names",
        "target_terms": (
            "list",
            "sora",
            "names",
        ),
    },
    {
        "name": "riyadh_saliheem",
        "query": "Riyadh us Saliheem",
        "target_terms": (
            "riyadh",
            "saliheem",
        ),
    },
    {
        "name": "la_ta7zan",
        "query": "la ta7zan",
        "target_terms": (
            "la",
            "ta7zan",
        ),
    },
    {
        "name": "kameez_pattern",
        "query": "kameez pattern",
        "target_terms": (
            "kameez",
            "pattern",
        ),
    },
    {
        "name": "guerilla_warfare",
        "query": "Guevara Che Guerilla Warfare",
        "target_terms": (
            "guevara",
            "guerilla",
            "warfare",
        ),
    },
    {
        "name": "lane_lexicon",
        "query": "Edward William Lane Arabic English Lexicon Vol 6",
        "target_terms": (
            "edward",
            "william",
            "lane",
            "arabic",
            "english",
            "lexicon",
            "vol",
            "6",
        ),
    },
)


ADVERSARIAL = (
    "quantum upholstery banana zeppelin",
    "medieval sourdough GPU firmware",
    "hydraulic pastry compiler astronomy",
    "volcanic spreadsheet penguin firmware",
    "ceramic database pineapple cavalry",
    "orbital sandwich kernel theology",
    "Victorian Kubernetes broccoli engine",
    "submarine pastry JavaScript cathedral",
    "neural gearbox cinnamon telescope",
    "Apache helicopter sourdough recursion violin",
)


SEMANTIC_REGRESSION = (
    (
        "ai_assisted_python",
        "AI assisted Python programming",
    ),
    (
        "cpp",
        "C++ programming",
    ),
    (
        "effective_c",
        "effective C programming",
    ),
    (
        "civil_defense",
        "civil defense manual",
    ),
    (
        "army_survival",
        "US Army survival manual",
    ),
    (
        "electronics",
        "practical electronics handbook",
    ),
    (
        "marx",
        "Marx mathematical manuscripts",
    ),
)


# ------------------------------------------------------------
# TARGET SELECTION
# ------------------------------------------------------------

def choose_target(
    rows: list[Mapping[str, Any]],
    terms: tuple[str, ...],
) -> tuple[int | None, Mapping[str, Any] | None]:
    wanted = tuple(
        identity_normalize(term)
        for term in terms
    )

    best_index = None
    best_row = None
    best_score = -1

    for index, row in enumerate(rows, start=1):
        title = identity_normalize(
            title_of(row)
        )

        score = sum(
            1
            for term in wanted
            if term and term in title
        )

        if score > best_score:
            best_score = score
            best_index = index
            best_row = row

    required = max(
        1,
        min(
            len(wanted),
            2,
        ),
    )

    if best_score < required:
        return None, None

    return best_index, best_row


# ------------------------------------------------------------
# MAIN
# ------------------------------------------------------------

def main() -> int:
    started = time.time()

    OUTDIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    print("=" * 72)
    print(" GENESIS RECALL R2-R2A")
    print(" QUALIFICATION SUBJECT SEMANTICS")
    print(" + IDENTITY ALIAS SHADOW REPAIR")
    print("=" * 72)

    # Explicit read-only database contract.
    uri = f"file:{DB}?mode=ro"

    con = sqlite3.connect(
        uri,
        uri=True,
    )

    try:
        con.execute(
            "PRAGMA query_only=ON"
        )

        query_only = con.execute(
            "PRAGMA query_only"
        ).fetchone()[0]

        integrity = con.execute(
            "PRAGMA integrity_check"
        ).fetchone()[0]

    finally:
        con.close()

    print()
    print("=== READ-ONLY DB CONTRACT ===")
    print("query_only :", query_only)
    print("integrity  :", integrity)

    if query_only != 1:
        print("FAIL: query_only not active")
        return 2

    if integrity != "ok":
        print("FAIL: DB integrity")
        return 2

    engine = QualificationEngine()

    thresholds = engine.thresholds

    accept_threshold = float(
        thresholds.accept
    )

    print()
    print("=== ACTIVE QUALIFICATION THRESHOLDS ===")
    print("accept             :", thresholds.accept)
    print(
        "minimum_confidence :",
        thresholds.minimum_confidence,
    )
    print(
        "minimum_lexical    :",
        thresholds.minimum_lexical,
    )
    print(
        "minimum_subject    :",
        thresholds.minimum_subject,
    )

    results = []

    print()
    print("=== A. SUBJECT + IDENTITY ALIAS MATRIX ===")

    for canary in CANARIES:
        name = canary["name"]
        query = canary["query"]

        raw = search_catalog(
            query,
            db_path=DB,
            limit=100,
        )

        rank, row = choose_target(
            raw,
            canary["target_terms"],
        )

        print()
        print("-" * 72)
        print(name)
        print("query :", query)

        if row is None:
            result = {
                "name": name,
                "query": query,
                "raw_rank": None,
                "found": False,
                "pass": False,
            }

            results.append(result)

            print("TARGET: NOT FOUND")
            continue

        rid = runtime_id(row)
        title = title_of(row)

        accepted, evidence = qualification_for(
            query,
            row,
            engine,
        )

        fields = evidence_fields(
            evidence
        )

        alias = identity_alias_analysis(
            query,
            title,
        )

        baseline_accepted = bool(
            accepted
        )

        shadow = shadow_identity_qualification(
            alias=alias,
            fields=fields,
            accepted_baseline=baseline_accepted,
            deterministic_identity_hit=True,
            accept_threshold=accept_threshold,
        )

        result = {
            "name": name,
            "query": query,
            "runtime_id": rid,
            "raw_rank": rank,
            "title": title,
            "found": True,
            "baseline_accepted": baseline_accepted,
            "qualification": fields,
            "identity_alias": alias,
            "shadow": shadow,
        }

        if name == "lane_lexicon":
            result["pass"] = bool(
                shadow["accepted"]
                and shadow["reason"]
                == "deterministic_identity_alias_subject_repair"
            )
        else:
            result["pass"] = bool(
                baseline_accepted
                or shadow["accepted"]
            )

        results.append(result)

        print("runtime id        :", rid)
        print("raw rank          :", rank)
        print("title             :", title)
        print(
            "baseline decision :",
            fields.get("decision"),
        )
        print(
            "baseline subject  :",
            fields.get("score_subject"),
        )
        print(
            "baseline lexical  :",
            fields.get("score_lexical"),
        )
        print(
            "baseline final    :",
            fields.get("score_final"),
        )
        print(
            "baseline prov     :",
            fields.get("score_provenance"),
        )

        print()
        print("identity query     :", alias["query_normalized"])
        print("identity title     :", alias["title_normalized"])
        print("token coverage     :", alias["coverage"])
        print("ordered subseq     :", alias["ordered"])
        print("identity alias     :", alias["identity_alias"])

        print()
        print("shadow accepted    :", shadow["accepted"])
        print("shadow reason      :", shadow["reason"])
        print("PASS               :", result["pass"])

    # --------------------------------------------------------
    # Lane token anatomy
    # --------------------------------------------------------

    print()
    print("=== B. LANE TOKEN-BY-TOKEN ANATOMY ===")

    lane = next(
        (
            item
            for item in results
            if item["name"] == "lane_lexicon"
        ),
        None,
    )

    lane_anatomy_pass = False

    if lane and lane.get("found"):
        alias = lane["identity_alias"]

        qtokens = alias["query_tokens"]
        ttokens = set(
            alias["title_tokens"]
        )

        for token in qtokens:
            print(
                f"{token:<20} ->",
                "MATCH"
                if token in ttokens
                else "MISS",
            )

        lane_anatomy_pass = (
            alias["coverage"] == 1.0
            and alias["ordered"]
            and alias["identity_alias"]
        )

    print(
        "LANE IDENTITY ANATOMY:",
        "PASS"
        if lane_anatomy_pass
        else "FAIL",
    )

    # --------------------------------------------------------
    # Existing semantic regression
    # --------------------------------------------------------

    print()
    print("=== C. EXISTING SEMANTIC REGRESSION ===")

    semantic_results = []

    for name, query in SEMANTIC_REGRESSION:
        raw = search_catalog(
            query,
            db_path=DB,
            limit=20,
        )

        accepted, result = qualify_rows(
            query,
            raw,
            engine=engine,
        )

        passed = bool(
            accepted
        )

        semantic_results.append(
            {
                "name": name,
                "query": query,
                "raw_results": len(raw),
                "qualified_results": len(accepted),
                "pass": passed,
            }
        )

        print(
            f"{name:<24}",
            f"raw={len(raw):<4}",
            f"qualified={len(accepted):<4}",
            f"PASS={passed}",
        )

    semantic_pass = all(
        item["pass"]
        for item in semantic_results
    )

    # --------------------------------------------------------
    # Adversarial identity alias controls
    # --------------------------------------------------------

    print()
    print("=== D. ADVERSARIAL IDENTITY ALIAS CONTROLS ===")

    adversarial_results = []

    for query in ADVERSARIAL:
        raw = search_catalog(
            query,
            db_path=DB,
            limit=100,
        )

        aliases = []

        for rank, row in enumerate(raw, start=1):
            title = title_of(row)

            alias = identity_alias_analysis(
                query,
                title,
            )

            if alias["identity_alias"]:
                aliases.append(
                    {
                        "rank": rank,
                        "runtime_id": runtime_id(row),
                        "title": title,
                        "alias": alias,
                    }
                )

        passed = len(aliases) == 0

        adversarial_results.append(
            {
                "query": query,
                "raw_results": len(raw),
                "identity_aliases": aliases,
                "pass": passed,
            }
        )

        print()
        print("query          :", query)
        print("raw candidates :", len(raw))
        print("alias matches  :", len(aliases))
        print("PASS           :", passed)

    adversarial_pass = all(
        item["pass"]
        for item in adversarial_results
    )

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    catalog_pass = all(
        item.get("pass", False)
        for item in results
    )

    lane_shadow_pass = bool(
        lane
        and lane.get("pass")
    )

    shadow_certified = (
        catalog_pass
        and lane_anatomy_pass
        and lane_shadow_pass
        and semantic_pass
        and adversarial_pass
    )

    elapsed = time.time() - started

    payload = {
        "pack": "Genesis Recall R2-R2A",
        "mode": "shadow",
        "production_source_changes": 0,
        "production_db_writes": 0,
        "llm_calls": 0,
        "thresholds": jsonable(
            thresholds
        ),
        "catalog_canaries": results,
        "lane_identity_anatomy_pass": lane_anatomy_pass,
        "lane_shadow_pass": lane_shadow_pass,
        "semantic_regression": semantic_results,
        "semantic_regression_pass": semantic_pass,
        "adversarial": adversarial_results,
        "adversarial_pass": adversarial_pass,
        "catalog_pass": catalog_pass,
        "shadow_certified": shadow_certified,
        "elapsed_seconds": elapsed,
    }

    REPORT.write_text(
        json.dumps(
            payload,
            indent=2,
            sort_keys=True,
            default=str,
        ),
        encoding="utf-8",
    )

    with TSV.open(
        "w",
        encoding="utf-8",
    ) as fh:
        fh.write(
            "\t".join(
                (
                    "name",
                    "runtime_id",
                    "raw_rank",
                    "baseline_decision",
                    "subject_score",
                    "lexical_score",
                    "final_score",
                    "identity_coverage",
                    "identity_ordered",
                    "identity_alias",
                    "shadow_accepted",
                    "shadow_reason",
                    "pass",
                )
            )
            + "\n"
        )

        for item in results:
            q = item.get(
                "qualification",
                {},
            )

            alias = item.get(
                "identity_alias",
                {},
            )

            shadow = item.get(
                "shadow",
                {},
            )

            fh.write(
                "\t".join(
                    str(value)
                    for value in (
                        item.get("name"),
                        item.get("runtime_id"),
                        item.get("raw_rank"),
                        q.get("decision"),
                        q.get("score_subject"),
                        q.get("score_lexical"),
                        q.get("score_final"),
                        alias.get("coverage"),
                        alias.get("ordered"),
                        alias.get("identity_alias"),
                        shadow.get("accepted"),
                        shadow.get("reason"),
                        item.get("pass"),
                    )
                )
                + "\n"
            )

    print()
    print("=" * 72)
    print(" GENESIS RECALL R2-R2A SHADOW RESULT")
    print("=" * 72)
    print(
        "catalog canaries       :",
        "PASS" if catalog_pass else "FAIL",
    )
    print(
        "Lane identity anatomy  :",
        "PASS" if lane_anatomy_pass else "FAIL",
    )
    print(
        "Lane shadow repair     :",
        "PASS" if lane_shadow_pass else "FAIL",
    )
    print(
        "semantic regression    :",
        "PASS" if semantic_pass else "FAIL",
    )
    print(
        "adversarial aliases    :",
        "PASS" if adversarial_pass else "FAIL",
    )
    print()
    print(
        "R2-R2A CERTIFIED       :",
        shadow_certified,
    )
    print(
        "elapsed seconds        :",
        round(elapsed, 2),
    )
    print(
        "production source edits:",
        0,
    )
    print(
        "production DB writes   :",
        0,
    )
    print("=" * 72)

    return 0 if shadow_certified else 1


if __name__ == "__main__":
    raise SystemExit(main())
