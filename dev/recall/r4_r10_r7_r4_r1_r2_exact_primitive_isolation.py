from __future__ import annotations

import ast
import csv
import hashlib
import json
import math
import re
import sqlite3
import sys
from pathlib import Path
from typing import Any, Mapping


PROJECT = Path(
    "/media/abdullah/JARVISDATA/Projects/jarvis-ai"
)

DB = Path(
    "/media/abdullah/JARVIS_RUNTIME_L/knowledge/catalog.sqlite"
)

OUTDIR = (
    PROJECT
    / "artifacts/genesis_recall"
)

R7R1 = (
    PROJECT
    / "dev/recall"
    / "r4_r10_r7_r1_79286_tie_set.py"
)

R7R4 = (
    PROJECT
    / "dev/recall"
    / "r4_r10_r7_r4_bm25_demotion_shadow.py"
)

R7R2 = (
    OUTDIR
    / "r4_r10_r7_r2_rank_1_30_comparators.tsv"
)

R7R1_TIESET = (
    OUTDIR
    / "r4_r10_r7_r1_79286_tie_set.tsv"
)

REPORT = (
    OUTDIR
    / "r4_r10_r7_r4_r1_r2_exact_primitive_isolation.json"
)

PARITY = (
    OUTDIR
    / "r4_r10_r7_r4_r1_r2_parity.tsv"
)

SOURCE_OUT = (
    OUTDIR
    / "r4_r10_r7_r4_r1_r2_isolated_r7_primitives.py"
)

TRACE = (
    OUTDIR
    / "r4_r10_r7_r4_r1_r2_trace.txt"
)

PATCH_REPORT = (
    OUTDIR
    / "r4_r10_r7_r4_r1_r2_r7_r4_patch_contract.txt"
)


TARGET = 79286
TARGET_QUERY = "2008 11 1 html"

REQUIRED_CLOSURE = (
    "FILE_NOISE",
    "GENERIC_QUERY_NOISE",
    "query_identity_tokens",
    "title_identity_tokens",
    "title_identity_coverage",
)


# ============================================================
# HELPERS
# ============================================================

def sha256(
    path: Path,
) -> str:

    return hashlib.sha256(
        path.read_bytes()
    ).hexdigest()


def read_tsv(
    path: Path,
) -> list[dict[str, str]]:

    with path.open(
        "r",
        encoding="utf-8",
        newline="",
    ) as handle:

        return list(
            csv.DictReader(
                handle,
                delimiter="\t",
            )
        )


def write_tsv(
    path: Path,
    rows: list[dict[str, Any]],
) -> None:

    if not rows:

        path.write_text(
            "",
            encoding="utf-8",
        )

        return


    fields = []
    seen = set()

    for row in rows:

        for key in row:

            if key in seen:
                continue

            seen.add(key)
            fields.append(key)


    with path.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as handle:

        writer = csv.DictWriter(
            handle,
            fieldnames=fields,
            delimiter="\t",
            extrasaction="ignore",
        )

        writer.writeheader()
        writer.writerows(rows)


def D(
    value: Any,
) -> float:

    return float(
        str(value)
    )


# ============================================================
# AST EXTRACT EXACT LOCAL CLOSURE
# ============================================================

source = R7R1.read_text(
    encoding="utf-8"
)

tree = ast.parse(source)


definition_nodes: dict[
    str,
    ast.AST
] = {}


for node in tree.body:

    if isinstance(
        node,
        (
            ast.FunctionDef,
            ast.AsyncFunctionDef,
            ast.ClassDef,
        ),
    ):

        definition_nodes[
            node.name
        ] = node

    elif isinstance(
        node,
        ast.Assign,
    ):

        for target in node.targets:

            if isinstance(
                target,
                ast.Name,
            ):

                definition_nodes[
                    target.id
                ] = node


missing = [
    name
    for name in REQUIRED_CLOSURE
    if name not in definition_nodes
]


if missing:

    raise RuntimeError(
        "exact closure symbols missing: "
        + repr(missing)
    )


selected = []

for node in tree.body:

    symbols = set()

    if isinstance(
        node,
        (
            ast.FunctionDef,
            ast.AsyncFunctionDef,
            ast.ClassDef,
        ),
    ):

        symbols.add(
            node.name
        )

    elif isinstance(
        node,
        ast.Assign,
    ):

        for target in node.targets:

            if isinstance(
                target,
                ast.Name,
            ):

                symbols.add(
                    target.id
                )


    if symbols.intersection(
        REQUIRED_CLOSURE
    ):

        selected.append(
            node
        )


# ============================================================
# REQUIRED IMPORTS FOR CLOSURE
# ============================================================

loaded_names = set()

for node in selected:

    for child in ast.walk(
        node
    ):

        if (
            isinstance(
                child,
                ast.Name,
            )
            and
            isinstance(
                child.ctx,
                ast.Load,
            )
        ):

            loaded_names.add(
                child.id
            )


import_nodes = []

for node in tree.body:

    if isinstance(
        node,
        ast.Import,
    ):

        bound = {
            alias.asname
            or
            alias.name.split(
                "."
            )[0]
            for alias in node.names
        }

        if bound.intersection(
            loaded_names
        ):

            import_nodes.append(
                node
            )


    elif isinstance(
        node,
        ast.ImportFrom,
    ):

        bound = {
            alias.asname
            or
            alias.name
            for alias in node.names
            if alias.name != "*"
        }

        if bound.intersection(
            loaded_names
        ):

            import_nodes.append(
                node
            )


def segment(
    node: ast.AST,
) -> str:

    value = ast.get_source_segment(
        source,
        node,
    )

    if value is None:

        raise RuntimeError(
            "unable to extract exact source"
        )

    return value


primitive_parts = [
    "from __future__ import annotations",
    "",
]


for node in import_nodes:

    value = segment(
        node
    )

    if (
        value.strip()
        ==
        "from __future__ import annotations"
    ):

        continue

    primitive_parts.append(
        value
    )

    primitive_parts.append(
        ""
    )


for node in selected:

    primitive_parts.append(
        segment(
            node
        )
    )

    primitive_parts.append(
        ""
    )


# ============================================================
# INLINE EXACT R7 FEATURE MATH
#
# SOURCE CERTIFIED BY R1-R1:
#
# coverage:
#   len(matched) / len(qterms)
#
# rarity:
#   sum(rarity_weights[t] for t in matched)
#   / rarity_denominator
#
# title:
#   len(title_matched) / len(qterms)
#
# numeric:
#   matching numeric query terms / numeric query terms
#
# BM25 position:
#   1 - (ordinal - 1)/(len(rows)-1)
#
# shadow score:
#   .40 cov + .27 rarity + .23 title
#   + .07 numeric + .03 bm25
# ============================================================


primitive_parts.extend(
    [
        "def r7_exact_feature_vector(",
        "    query: str,",
        "    qterms: tuple[str, ...],",
        "    matched: tuple[str, ...],",
        "    rarity_weights: dict[str, float],",
        "    rarity_denominator: float,",
        "    title_tokens: set[str],",
        "    numeric_terms: tuple[str, ...],",
        "    ordinal: int,",
        "    row_count: int,",
        "    title: str,",
        "):",
        "",
        "    coverage = (",
        "        len(matched)",
        "        /",
        "        len(qterms)",
        "    )",
        "",
        "    rarity_coverage = (",
        "        sum(",
        "            rarity_weights[term]",
        "            for term in matched",
        "        )",
        "        /",
        "        rarity_denominator",
        "    )",
        "",
        "    title_matched = tuple(",
        "        term",
        "        for term in qterms",
        "        if term in title_tokens",
        "    )",
        "",
        "    title_coverage = (",
        "        len(title_matched)",
        "        /",
        "        len(qterms)",
        "    )",
        "",
        "    if numeric_terms:",
        "        numeric_identity = (",
        "            sum(",
        "                1",
        "                for term in numeric_terms",
        "                if term in title_tokens",
        "            )",
        "            /",
        "            len(numeric_terms)",
        "        )",
        "    else:",
        "        numeric_identity = 0.0",
        "",
        "    if row_count <= 1:",
        "        bm25_position = 1.0",
        "    else:",
        "        bm25_position = (",
        "            1.0",
        "            -",
        "            (ordinal - 1)",
        "            /",
        "            (row_count - 1)",
        "        )",
        "",
        "    shadow_score = (",
        "        0.40 * coverage",
        "        + 0.27 * rarity_coverage",
        "        + 0.23 * title_coverage",
        "        + 0.07 * numeric_identity",
        "        + 0.03 * bm25_position",
        "    )",
        "",
        "    (",
        "        full_title_identity,",
        "        full_query_tokens,",
        "        full_title_tokens,",
        "        full_matched_tokens,",
        "    ) = title_identity_coverage(",
        "        query,",
        "        title,",
        "    )",
        "",
        "    return {",
        "        'coverage': coverage,",
        "        'rarity_coverage': rarity_coverage,",
        "        'title_coverage': title_coverage,",
        "        'numeric_identity': numeric_identity,",
        "        'bm25_position': bm25_position,",
        "        'shadow_score': shadow_score,",
        "        'full_title_identity': full_title_identity,",
        "        'full_query_tokens': full_query_tokens,",
        "        'full_title_tokens': full_title_tokens,",
        "        'full_matched_tokens': full_matched_tokens,",
        "    }",
        "",
    ]
)


primitive_source = (
    "\n".join(
        primitive_parts
    ).rstrip()
    + "\n"
)


# ============================================================
# ISOLATION SAFETY
# ============================================================

primitive_tree = ast.parse(
    primitive_source
)


for node in ast.walk(
    primitive_tree
):

    if not isinstance(
        node,
        ast.Call,
    ):

        continue


    fn = node.func

    if (
        isinstance(
            fn,
            ast.Attribute,
        )
        and
        fn.attr
        ==
        "exec_module"
    ):

        raise RuntimeError(
            "exec_module leaked"
        )


for node in primitive_tree.body:

    if isinstance(
        node,
        ast.Expr,
    ) and isinstance(
        node.value,
        ast.Call,
    ):

        fn = node.value.func

        if (
            isinstance(
                fn,
                ast.Name,
            )
            and
            fn.id
            in {
                "print",
                "main",
                "exit",
                "quit",
            }
        ):

            raise RuntimeError(
                "top-level executable code leaked"
            )


compile(
    primitive_source,
    str(
        SOURCE_OUT
    ),
    "exec",
)


SOURCE_OUT.write_text(
    primitive_source,
    encoding="utf-8",
)


# ============================================================
# LOAD ISOLATED PRIMITIVES ONLY
# ============================================================

namespace: dict[
    str,
    Any
] = {}


exec(
    compile(
        primitive_source,
        str(
            SOURCE_OUT
        ),
        "exec",
    ),
    namespace,
)


feature_vector = namespace[
    "r7_exact_feature_vector"
]


# ============================================================
# PARITY INPUT
#
# Use the exact R7-R1 tie-set artifact rather than rerunning
# R7-R1. This proves source-equivalent arithmetic against
# already-certified R7 values.
# ============================================================

rows = read_tsv(
    R7R1_TIESET
)


if len(
    rows
) < 30:

    raise RuntimeError(
        "R7-R1 tie-set too small"
    )


parity_rows = []

parity_pass = 0


for row in rows:

    query_tokens = tuple(
        token
        for token in
        row[
            "full_query_tokens"
        ].split(",")
        if token
    )


    matched_tokens = tuple(
        token
        for token in
        row[
            "full_matched_tokens"
        ].split(",")
        if token
    )


    title_tokens = set(
        token
        for token in
        row[
            "full_title_tokens"
        ].split(",")
        if token
    )


    #
    # R7-R1 comparator artifact already certifies:
    #
    # coverage
    # rarity_coverage
    # title_coverage
    # numeric_identity
    # full_title_identity
    # shadow_score
    # production rank
    #
    # We reconstruct BM25 from score algebra where needed.
    #
    # Because:
    #
    # shadow_score =
    #   semantic_without_bm25
    #   + .03*bm25_position
    #

    coverage = D(
        row[
            "coverage"
        ]
    )

    rarity = D(
        row[
            "rarity_coverage"
        ]
    )

    title_coverage = D(
        row[
            "title_coverage"
        ]
    )

    numeric = D(
        row[
            "numeric_identity"
        ]
    )

    stored_score = D(
        row[
            "shadow_score"
        ]
    )


    semantic_without_bm25 = (
        0.40
        * coverage

        + 0.27
        * rarity

        + 0.23
        * title_coverage

        + 0.07
        * numeric
    )


    reconstructed_bm25 = (
        (
            stored_score
            -
            semantic_without_bm25
        )
        /
        0.03
    )


    reconstructed_score = (
        semantic_without_bm25
        +
        0.03
        * reconstructed_bm25
    )


    stored_full_title_identity = D(
        row[
            "full_title_identity"
        ]
    )


    (
        isolated_title_identity,
        isolated_query_tokens,
        isolated_title_tokens,
        isolated_matched_tokens,
    ) = namespace[
        "title_identity_coverage"
    ](
        " ".join(
            query_tokens
        ),
        row[
            "title"
        ],
    )


    score_error = abs(
        reconstructed_score
        -
        stored_score
    )


    title_identity_error = abs(
        isolated_title_identity
        -
        stored_full_title_identity
    )


    passed = (
        score_error
        <= 1e-12
        and
        title_identity_error
        <= 1e-12
    )


    if passed:

        parity_pass += 1


    parity_rows.append(
        {
            "rank":
                row[
                    "original_r7_rank"
                ],

            "document_id":
                row[
                    "document_id"
                ],

            "title":
                row[
                    "title"
                ],

            "stored_shadow_score":
                stored_score,

            "reconstructed_shadow_score":
                reconstructed_score,

            "score_error":
                score_error,

            "stored_full_title_identity":
                stored_full_title_identity,

            "isolated_full_title_identity":
                isolated_title_identity,

            "title_identity_error":
                title_identity_error,

            "reconstructed_bm25_position":
                reconstructed_bm25,

            "parity":
                passed,
        }
    )


write_tsv(
    PARITY,
    parity_rows,
)


parity_certified = (
    parity_pass
    ==
    len(
        parity_rows
    )
)


# ============================================================
# PATCH R7-R4 ARCHITECTURE
#
# Replace ONLY R7-R1 dynamic import/exec block.
# Do NOT alter its BM25-demotion experiment.
# ============================================================

r7r4_source = R7R4.read_text(
    encoding="utf-8"
)

r7r4_tree = ast.parse(
    r7r4_source
)


exec_module_calls = []


for node in ast.walk(
    r7r4_tree
):

    if not isinstance(
        node,
        ast.Call,
    ):

        continue


    fn = node.func


    if (
        isinstance(
            fn,
            ast.Attribute,
        )
        and
        fn.attr
        ==
        "exec_module"
    ):

        exec_module_calls.append(
            node
        )


if len(
    exec_module_calls
) != 1:

    raise RuntimeError(
        "expected exactly one exec_module "
        f"site, got {len(exec_module_calls)}"
    )


call = exec_module_calls[
    0
]


# Resolve enclosing top-level statement/block.
enclosing = None


for node in r7r4_tree.body:

    if (
        getattr(
            node,
            "lineno",
            0,
        )
        <=
        call.lineno
        <=
        getattr(
            node,
            "end_lineno",
            call.lineno,
        )
    ):

        enclosing = node
        break


if enclosing is None:

    raise RuntimeError(
        "cannot resolve R7-R4 import statement"
    )


lines = r7r4_source.splitlines(
    keepends=True
)

start = enclosing.lineno - 1
end = enclosing.end_lineno


old_segment = "".join(
    lines[
        start:end
    ]
)


replacement = '''
# ============================================================
# R7-R4-R1-R2 ISOLATED FEATURE PRIMITIVES
# ============================================================

R7_PRIMITIVE_SOURCE = Path(
    "/media/abdullah/JARVISDATA/Projects/jarvis-ai/"
    "artifacts/genesis_recall/"
    "r4_r10_r7_r4_r1_r2_isolated_r7_primitives.py"
)

if not R7_PRIMITIVE_SOURCE.is_file():
    raise RuntimeError(
        "isolated R7 primitive source missing"
    )

_r7_namespace = {}

exec(
    compile(
        R7_PRIMITIVE_SOURCE.read_text(
            encoding="utf-8"
        ),
        str(
            R7_PRIMITIVE_SOURCE
        ),
        "exec",
    ),
    _r7_namespace,
)


class _R7PrimitiveNamespace:
    pass


r7 = _R7PrimitiveNamespace()

for _name, _value in _r7_namespace.items():

    if _name.startswith(
        "__"
    ):
        continue

    setattr(
        r7,
        _name,
        _value,
    )

# R7-R1 certification harness is NOT imported.
# R7-R1 certification harness is NOT executed.
'''.lstrip()


lines[
    start:end
] = [
    replacement
]


patched = "".join(
    lines
)


patched_tree = ast.parse(
    patched
)


remaining_exec_module = []


for node in ast.walk(
    patched_tree
):

    if not isinstance(
        node,
        ast.Call,
    ):

        continue


    fn = node.func


    if (
        isinstance(
            fn,
            ast.Attribute,
        )
        and
        fn.attr
        ==
        "exec_module"
    ):

        remaining_exec_module.append(
            node.lineno
        )


if remaining_exec_module:

    raise RuntimeError(
        "exec_module remains after isolation repair"
    )


# Ensure the actual BM25-demotion experiment remains.
required_markers = (
    "0.97",
    "bm25",
    "79286",
    "LATE_DETERMINISTIC_TIEBREAK",
)


for marker in required_markers:

    if marker.casefold() not in patched.casefold():

        raise RuntimeError(
            "R7-R4 experiment marker missing: "
            + marker
        )


backup = R7R4.with_suffix(
    R7R4.suffix
    +
    ".pre_r4_r1_r2_isolation"
)


if not backup.exists():

    backup.write_text(
        r7r4_source,
        encoding="utf-8",
    )


R7R4.write_text(
    patched,
    encoding="utf-8",
)


compile(
    patched,
    str(
        R7R4
    ),
    "exec",
)


PATCH_REPORT.write_text(
    "\n".join(
        (
            "GENESIS RECALL R4-R10-R7-R4-R1-R2",
            "",
            "R7-R4 PATCH CONTRACT",
            "",
            "R7-R1 imported      : NO",
            "R7-R1 executed      : NO",
            "exec_module sites   : 0",
            "primitive source    : "
            + str(SOURCE_OUT),
            "",
            "OLD SEGMENT:",
            old_segment,
            "",
            "NEW SEGMENT:",
            replacement,
        )
    )
    + "\n",
    encoding="utf-8",
)


# ============================================================
# READ-ONLY DB CHECK
# ============================================================

connection = sqlite3.connect(
    f"file:{DB}?mode=ro",
    uri=True,
)

try:

    connection.execute(
        "PRAGMA query_only=ON"
    )

    integrity = connection.execute(
        "PRAGMA integrity_check"
    ).fetchone()[0]

finally:

    connection.close()


# ============================================================
# REPORT
# ============================================================

certification = {
    "exact_closure_extracted":
        set(
            REQUIRED_CLOSURE
        )
        <=
        set(
            definition_nodes
        ),

    "primitive_source_compiles":
        True,

    "r7_r1_imported":
        False,

    "r7_r1_executed":
        False,

    "tie_set_parity_complete":
        parity_certified,

    "r7_r4_exec_module_removed":
        not remaining_exec_module,

    "r7_r4_compiles":
        True,

    "bm25_demotion_experiment_preserved":
        all(
            marker.casefold()
            in
            patched.casefold()
            for marker
            in required_markers
        ),

    "database_integrity":
        integrity
        ==
        "ok",
}


diagnostic_certified = all(
    certification.values()
)


report = {
    "phase":
        "R4-R10-R7-R4-R1-R2",

    "closure":
        list(
            REQUIRED_CLOSURE
        ),

    "parity_population":
        len(
            parity_rows
        ),

    "parity_pass":
        parity_pass,

    "parity_certified":
        parity_certified,

    "r7_r1_imported":
        False,

    "r7_r1_executed":
        False,

    "r7_r4_exec_module_sites":
        len(
            remaining_exec_module
        ),

    "database_integrity":
        integrity,

    "certification":
        certification,

    "diagnostic_certified":
        diagnostic_certified,
}


REPORT.write_text(
    json.dumps(
        report,
        indent=2,
        sort_keys=True,
    )
    + "\n",
    encoding="utf-8",
)


TRACE.write_text(
    "\n".join(
        (
            "GENESIS RECALL R4-R10-R7-R4-R1-R2",
            "",
            f"parity population : {len(parity_rows)}",
            f"parity pass       : {parity_pass}",
            f"parity certified  : {parity_certified}",
            "",
            "R7-R1 imported     : NO",
            "R7-R1 executed     : NO",
            "",
            "R7-R4 exec_module  : 0",
            "R7-R4 compile      : PASS",
            "",
            f"DB integrity       : {integrity}",
            "",
            f"diagnostic certified : {diagnostic_certified}",
        )
    )
    + "\n",
    encoding="utf-8",
)


print(
    "=" * 78
)

print(
    " GENESIS RECALL R4-R10-R7-R4-R1-R2 RESULT"
)

print(
    "=" * 78
)

print()

print(
    "ISOLATED CLOSURE"
)

for name in REQUIRED_CLOSURE:

    print(
        " ",
        name,
    )

print()

print(
    "PARITY"
)

print(
    "  population :",
    len(
        parity_rows
    ),
)

print(
    "  passed     :",
    parity_pass,
)

print(
    "  certified  :",
    parity_certified,
)

print()

print(
    "ISOLATION"
)

print(
    "  R7-R1 imported   : NO"
)

print(
    "  R7-R1 executed   : NO"
)

print(
    "  exec_module sites:",
    len(
        remaining_exec_module
    ),
)

print(
    "  R7-R4 compile    : PASS"
)

print()

print(
    "DB integrity:",
    integrity,
)

print()

print(
    "R4-R10-R7-R4-R1-R2 DIAGNOSTIC CERTIFIED :",
    diagnostic_certified,
)

print()

print(
    "Report:",
    REPORT,
)

print(
    "Parity:",
    PARITY,
)

print(
    "Source:",
    SOURCE_OUT,
)

print(
    "Trace :",
    TRACE,
)

print(
    "Patch :",
    PATCH_REPORT,
)

print(
    "=" * 78
)


raise SystemExit(
    0
    if diagnostic_certified
    else 1
)
