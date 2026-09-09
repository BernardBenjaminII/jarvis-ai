from __future__ import annotations

import ast
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


PROJECT = Path(
    "/media/abdullah/JARVISDATA/Projects/jarvis-ai"
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

ENGINE = (
    PROJECT
    / "dev/recall"
    / "r4_r10_r7_exact_feature_engine.py"
)

OUTDIR = (
    PROJECT
    / "artifacts/genesis_recall"
)

REPORT = (
    OUTDIR
    / "r4_r10_r7_r4_r1_r2_r6_repair.json"
)

TRACE = (
    OUTDIR
    / "r4_r10_r7_r4_r1_r2_r6_trace.txt"
)

ENGINE_CONTRACT = (
    OUTDIR
    / "r4_r10_r7_r4_r1_r2_r6_engine_contract.txt"
)

BUILD_CONTRACT = (
    OUTDIR
    / "r4_r10_r7_r4_r1_r2_r6_build_features_contract.txt"
)


PRIMARY_NAMES = {
    "coverage",
    "rarity_coverage",
    "title_coverage",
    "numeric_identity",
    "bm25_position",
    "shadow_score",
    "full_title_identity",
}

LOOP_PREREQUISITES = {
    "title_tokens",
    "matched",
    "title_matched",
    "title",
}

PRELUDE_TARGETS = {
    "qterms",
    "candidate_token_sets",
    "rarity_weights",
    "rarity_denominator",
    "numeric_terms",
}

FALSE_R7_HELPERS = {
    "tokenize_query",
    "query_token_rarity",
    "coverage_score",
    "rarity_coverage_score",
    "title_coverage_score",
    "numeric_identity_score",
    "full_title_identity_score",
    "token_set_for_candidate",
}


def sha(path: Path) -> str:
    return hashlib.sha256(
        path.read_bytes()
    ).hexdigest()


def target_names(
    target: ast.AST,
) -> set[str]:

    if isinstance(
        target,
        ast.Name,
    ):
        return {target.id}

    if isinstance(
        target,
        (
            ast.Tuple,
            ast.List,
        ),
    ):
        result: set[str] = set()

        for child in target.elts:
            result.update(
                target_names(child)
            )

        return result

    return set()


def statement_stores(
    node: ast.AST,
) -> set[str]:

    result = set()

    for child in ast.walk(node):

        if (
            isinstance(
                child,
                ast.Name,
            )
            and
            isinstance(
                child.ctx,
                ast.Store,
            )
        ):
            result.add(
                child.id
            )

        elif isinstance(
            child,
            (
                ast.FunctionDef,
                ast.AsyncFunctionDef,
                ast.ClassDef,
            ),
        ):
            result.add(
                child.name
            )

    return result


def loaded_names(
    node: ast.AST,
) -> set[str]:

    return {
        child.id
        for child in ast.walk(node)
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
        )
    }


def segment(
    source: str,
    node: ast.AST,
) -> str:

    value = ast.get_source_segment(
        source,
        node,
    )

    if not value:
        raise RuntimeError(
            "unable to extract exact source at "
            f"line {getattr(node, 'lineno', '?')}"
        )

    return value


# ============================================================
# R7-R1 SOURCE ANALYSIS
# ============================================================

r7_source = R7R1.read_text(
    encoding="utf-8"
)

r7_tree = ast.parse(
    r7_source
)


#
# Find the unique shadow_score assignment.
#

shadow_assignments = []

for node in ast.walk(r7_tree):

    if not isinstance(
        node,
        (
            ast.Assign,
            ast.AnnAssign,
        ),
    ):
        continue

    targets = []

    if isinstance(node, ast.Assign):

        for target in node.targets:
            targets.extend(
                target_names(target)
            )

    else:

        targets.extend(
            target_names(
                node.target
            )
        )

    if "shadow_score" in targets:
        shadow_assignments.append(
            node
        )


#
# R6-R2 CERTIFIED SHADOW-SCORE SELECTOR
#
# R5-R1 certified the production-equivalent R7 shadow-score
# producer at source line 911.
#
# R7-R1 contains multiple AST assignments named shadow_score,
# therefore symbol-name uniqueness is NOT a valid selector.
#

CERTIFIED_SHADOW_SCORE_LINE = 911

certified_shadow_assignments = [
    node
    for node in shadow_assignments
    if node.lineno
    ==
    CERTIFIED_SHADOW_SCORE_LINE
]


if len(
    certified_shadow_assignments
) != 1:

    raise RuntimeError(
        "certified shadow_score producer unavailable: "
        f"line={CERTIFIED_SHADOW_SCORE_LINE}, "
        f"matches={len(certified_shadow_assignments)}, "
        f"all_lines={[node.lineno for node in shadow_assignments]}"
    )


shadow = certified_shadow_assignments[0]


#
# Find enclosing top-level function.
#

owner = None

for node in r7_tree.body:

    if not isinstance(
        node,
        (
            ast.FunctionDef,
            ast.AsyncFunctionDef,
        ),
    ):
        continue

    if (
        node.lineno
        <=
        shadow.lineno
        <=
        getattr(
            node,
            "end_lineno",
            node.lineno,
        )
    ):
        owner = node
        break


if owner is None:

    raise RuntimeError(
        "could not identify enclosing R7 feature function"
    )


#
# Find the loop containing shadow_score.
#

feature_loop = None

for node in ast.walk(owner):

    if not isinstance(
        node,
        (
            ast.For,
            ast.AsyncFor,
        ),
    ):
        continue

    if (
        node.lineno
        <=
        shadow.lineno
        <=
        getattr(
            node,
            "end_lineno",
            node.lineno,
        )
    ):
        feature_loop = node
        break


if feature_loop is None:

    raise RuntimeError(
        "could not identify feature loop"
    )


# ============================================================
# PRELUDE SELECTION
# ============================================================

prelude_nodes: list[ast.stmt] = []

prelude_found: dict[
    str,
    ast.stmt
] = {}


for statement in owner.body:

    if statement is feature_loop:
        break

    stores = statement_stores(
        statement
    )

    for name in PRELUDE_TARGETS:

        if name in stores:
            prelude_found[
                name
            ] = statement


missing_prelude = sorted(
    PRELUDE_TARGETS
    -
    set(
        prelude_found
    )
)


if missing_prelude:

    raise RuntimeError(
        "missing exact R7 prelude producers: "
        + repr(
            missing_prelude
        )
    )


#
# Preserve original statement order and de-duplicate.
#

seen = set()

for statement in owner.body:

    if statement is feature_loop:
        break

    if statement not in prelude_found.values():
        continue

    if id(statement) in seen:
        continue

    seen.add(
        id(statement)
    )

    prelude_nodes.append(
        statement
    )


# ============================================================
# LOOP PRODUCER SELECTION
# ============================================================

selected_loop_nodes: list[
    ast.stmt
] = []


for statement in feature_loop.body:

    stores = statement_stores(
        statement
    )

    if stores & (
        PRIMARY_NAMES
        |
        LOOP_PREREQUISITES
    ):

        selected_loop_nodes.append(
            statement
        )


required_loop_outputs = (
    PRIMARY_NAMES
    |
    LOOP_PREREQUISITES
)


actual_loop_outputs = set()

for statement in selected_loop_nodes:

    actual_loop_outputs.update(
        statement_stores(
            statement
        )
    )


missing_loop = sorted(
    required_loop_outputs
    -
    actual_loop_outputs
)


if missing_loop:

    raise RuntimeError(
        "missing R7 loop producer statements: "
        + repr(
            missing_loop
        )
    )


# ============================================================
# TOP-LEVEL DEPENDENCY CLOSURE
# ============================================================

top_defs: dict[
    str,
    ast.stmt
] = {}

imports: list[
    ast.stmt
] = []


for node in r7_tree.body:

    if isinstance(
        node,
        (
            ast.Import,
            ast.ImportFrom,
        ),
    ):
        imports.append(
            node
        )
        continue

    if isinstance(
        node,
        (
            ast.FunctionDef,
            ast.AsyncFunctionDef,
            ast.ClassDef,
        ),
    ):

        top_defs[
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

                top_defs[
                    target.id
                ] = node

    elif isinstance(
        node,
        ast.AnnAssign,
    ):

        if isinstance(
            node.target,
            ast.Name,
        ):

            top_defs[
                node.target.id
            ] = node


seed_loaded = set()

for node in (
    *prelude_nodes,
    *selected_loop_nodes,
):

    seed_loaded.update(
        loaded_names(
            node
        )
    )


#
# Names provided locally by exact_feature_rows itself.
#

locally_bound = {
    "query",
    "rows",
    "ranked_features",
    "ordinal",
    "row",
    "tokens",
}


needed_top = {
    name
    for name in seed_loaded
    if (
        name in top_defs
        and
        name not in locally_bound
    )
}


frontier = list(
    needed_top
)

closure = set(
    needed_top
)


while frontier:

    name = frontier.pop(0)

    node = top_defs[
        name
    ]

    for dependency in loaded_names(
        node
    ):

        if dependency not in top_defs:
            continue

        if dependency in closure:
            continue

        closure.add(
            dependency
        )

        frontier.append(
            dependency
        )


#
# Preserve R7 top-level ordering.
#

closure_nodes = []

closure_node_ids = set()

for node in r7_tree.body:

    names = statement_stores(
        node
    )

    if not (
        names
        &
        closure
    ):
        continue

    if id(node) in closure_node_ids:
        continue

    closure_node_ids.add(
        id(node)
    )

    closure_nodes.append(
        node
    )


#
# Imports used by the closure or selected producer code.
#

all_loaded = set(
    seed_loaded
)

for node in closure_nodes:

    all_loaded.update(
        loaded_names(
            node
        )
    )


def import_bindings(
    node: ast.stmt,
) -> set[str]:

    result = set()

    if isinstance(
        node,
        ast.Import,
    ):

        for alias in node.names:

            result.add(
                alias.asname
                or
                alias.name.split(
                    "."
                )[0]
            )

    elif isinstance(
        node,
        ast.ImportFrom,
    ):

        for alias in node.names:

            if alias.name == "*":
                continue

            result.add(
                alias.asname
                or
                alias.name
            )

    return result


selected_imports = [
    node
    for node in imports
    if (
        import_bindings(
            node
        )
        &
        all_loaded
    )
]


# ============================================================
# BUILD EXACT FEATURE ENGINE
# ============================================================

# ============================================================
# BUILD EXACT FEATURE ENGINE — R6-R3 AST-SAFE SYNTHESIS
# ============================================================

import copy


#
# Preserve the exact already-selected R7 prerequisite
# statements as AST nodes instead of reindenting source text.
#


# ============================================================
# R6-R5-R2 EXACT CERTIFIED PRELUDE PRODUCER TRANSPLANT
# ============================================================

R6_R5_R2_REQUIRED_PRELUDE_PRODUCERS = (
    "document_frequency",
    "total_candidates",
)


def _r6_r5_r2_target_names(node):

    result = set()

    if isinstance(
        node,
        ast.Name,
    ):

        result.add(
            node.id
        )

    elif isinstance(
        node,
        (
            ast.Tuple,
            ast.List,
        ),
    ):

        for child in node.elts:

            result.update(
                _r6_r5_r2_target_names(
                    child
                )
            )

    return result


def _r6_r5_r2_assigned_names(node):

    result = set()

    if isinstance(
        node,
        ast.Assign,
    ):

        for target in node.targets:

            result.update(
                _r6_r5_r2_target_names(
                    target
                )
            )

    elif isinstance(
        node,
        ast.AnnAssign,
    ):

        result.update(
            _r6_r5_r2_target_names(
                node.target
            )
        )

    return result


#
# Recover producers ONLY from the already-certified R7-R1
# owner function selected by the persistent repair pipeline.
#

_r6_r5_r2_producers = {}


for _r6_r5_r2_node in owner.body:

    if not isinstance(
        _r6_r5_r2_node,
        (
            ast.Assign,
            ast.AnnAssign,
        ),
    ):

        continue

    _r6_r5_r2_names = (
        _r6_r5_r2_assigned_names(
            _r6_r5_r2_node
        )
    )


    for _r6_r5_r2_name in (
        R6_R5_R2_REQUIRED_PRELUDE_PRODUCERS
    ):

        if (
            _r6_r5_r2_name
            in
            _r6_r5_r2_names
        ):

            if (
                _r6_r5_r2_name
                in
                _r6_r5_r2_producers
            ):

                raise RuntimeError(
                    "duplicate certified R7-R1 "
                    "producer for "
                    + _r6_r5_r2_name
                )

            _r6_r5_r2_producers[
                _r6_r5_r2_name
            ] = _r6_r5_r2_node


_r6_r5_r2_missing = [
    name
    for name in
    R6_R5_R2_REQUIRED_PRELUDE_PRODUCERS
    if name
    not in
    _r6_r5_r2_producers
]


if _r6_r5_r2_missing:

    raise RuntimeError(
        "certified prelude producer missing: "
        + repr(
            _r6_r5_r2_missing
        )
    )


#
# Preserve the exact certified order:
#
#   document_frequency
#   total_candidates
#
# They must exist before rarity_weights.
#

_r6_r5_r2_ordered = [
    copy.deepcopy(
        _r6_r5_r2_producers[
            name
        ]
    )
    for name in
    R6_R5_R2_REQUIRED_PRELUDE_PRODUCERS
]


#
# Remove any prior copy of these producer names from
# prelude_nodes to prevent accidental duplication.
#

_r6_r5_r2_clean_prelude = []


for _r6_r5_r2_node in prelude_nodes:

    _r6_r5_r2_names = set()

    if isinstance(
        _r6_r5_r2_node,
        (
            ast.Assign,
            ast.AnnAssign,
        ),
    ):

        _r6_r5_r2_names = (
            _r6_r5_r2_assigned_names(
                _r6_r5_r2_node
            )
        )


    if (
        _r6_r5_r2_names
        &
        set(
            R6_R5_R2_REQUIRED_PRELUDE_PRODUCERS
        )
    ):

        continue


    _r6_r5_r2_clean_prelude.append(
        _r6_r5_r2_node
    )


#
# Locate rarity_weights in current prelude and insert the
# exact recovered producers immediately before it.
#

_r6_r5_r2_new_prelude = []

_r6_r5_r2_inserted = False


for _r6_r5_r2_node in (
    _r6_r5_r2_clean_prelude
):

    _r6_r5_r2_names = set()

    if isinstance(
        _r6_r5_r2_node,
        (
            ast.Assign,
            ast.AnnAssign,
        ),
    ):

        _r6_r5_r2_names = (
            _r6_r5_r2_assigned_names(
                _r6_r5_r2_node
            )
        )


    if (
        "rarity_weights"
        in
        _r6_r5_r2_names
        and
        not
        _r6_r5_r2_inserted
    ):

        _r6_r5_r2_new_prelude.extend(
            _r6_r5_r2_ordered
        )

        _r6_r5_r2_inserted = True


    _r6_r5_r2_new_prelude.append(
        _r6_r5_r2_node
    )


if not _r6_r5_r2_inserted:

    raise RuntimeError(
        "rarity_weights prelude anchor unavailable"
    )


prelude_nodes = (
    _r6_r5_r2_new_prelude
)

# ============================================================
# END R6-R5-R2 EXACT PRODUCER TRANSPLANT
# ============================================================

engine_body = []


for node in prelude_nodes:

    engine_body.append(
        copy.deepcopy(
            node
        )
    )


engine_body.append(
    ast.Assign(
        targets=[
            ast.Name(
                id="ranked_features",
                ctx=ast.Store(),
            )
        ],
        value=ast.List(
            elts=[],
            ctx=ast.Load(),
        ),
    )
)


#
# Recreate only the wrapper loop structure.
#
# The loop BODY is composed from exact deep-copies of the
# selected R7 producer statements. Nested if/else structures
# therefore retain their AST semantics automatically.
#

loop_target = ast.Tuple(
    elts=[
        ast.Name(
            id="ordinal",
            ctx=ast.Store(),
        ),
        ast.Tuple(
            elts=[
                ast.Name(
                    id="row",
                    ctx=ast.Store(),
                ),
                ast.Name(
                    id="tokens",
                    ctx=ast.Store(),
                ),
            ],
            ctx=ast.Store(),
        ),
    ],
    ctx=ast.Store(),
)


loop_iter = ast.Call(
    func=ast.Name(
        id="enumerate",
        ctx=ast.Load(),
    ),
    args=[
        ast.Call(
            func=ast.Name(
                id="zip",
                ctx=ast.Load(),
            ),
            args=[
                ast.Name(
                    id="rows",
                    ctx=ast.Load(),
                ),
                ast.Name(
                    id="candidate_token_sets",
                    ctx=ast.Load(),
                ),
            ],
            keywords=[],
        )
    ],
    keywords=[
        ast.keyword(
            arg="start",
            value=ast.Constant(
                value=1,
            ),
        )
    ],
)


loop_body = [
    copy.deepcopy(
        node
    )
    for node in selected_loop_nodes
]


loop_body.append(
    ast.Expr(
        value=ast.Call(
            func=ast.Attribute(
                value=ast.Name(
                    id="ranked_features",
                    ctx=ast.Load(),
                ),
                attr="append",
                ctx=ast.Load(),
            ),
            args=[
                ast.Dict(
                    keys=[
                        ast.Constant(
                            value="row"
                        ),
                        ast.Constant(
                            value="production_rank"
                        ),
                        ast.Constant(
                            value="coverage"
                        ),
                        ast.Constant(
                            value="rarity_coverage"
                        ),
                        ast.Constant(
                            value="title_coverage"
                        ),
                        ast.Constant(
                            value="numeric_identity"
                        ),
                        ast.Constant(
                            value="bm25_position"
                        ),
                        ast.Constant(
                            value="r7_score"
                        ),
                        ast.Constant(
                            value="full_title_identity"
                        ),
                    ],
                    values=[
                        ast.Name(
                            id="row",
                            ctx=ast.Load(),
                        ),
                        ast.Name(
                            id="ordinal",
                            ctx=ast.Load(),
                        ),
                        ast.Name(
                            id="coverage",
                            ctx=ast.Load(),
                        ),
                        ast.Name(
                            id="rarity_coverage",
                            ctx=ast.Load(),
                        ),
                        ast.Name(
                            id="title_coverage",
                            ctx=ast.Load(),
                        ),
                        ast.Name(
                            id="numeric_identity",
                            ctx=ast.Load(),
                        ),
                        ast.Name(
                            id="bm25_position",
                            ctx=ast.Load(),
                        ),
                        ast.Name(
                            id="shadow_score",
                            ctx=ast.Load(),
                        ),
                        ast.Name(
                            id="full_title_identity",
                            ctx=ast.Load(),
                        ),
                    ],
                )
            ],
            keywords=[],
        )
    )
)


engine_body.append(
    ast.For(
        target=loop_target,
        iter=loop_iter,
        body=loop_body,
        orelse=[],
    )
)


engine_body.append(
    ast.Return(
        value=ast.Name(
            id="ranked_features",
            ctx=ast.Load(),
        )
    )
)


function = ast.FunctionDef(
    name="exact_feature_rows",

    args=ast.arguments(
        posonlyargs=[],

        args=[
            ast.arg(
                arg="query"
            ),
            ast.arg(
                arg="rows"
            ),
        ],

        vararg=None,
        kwonlyargs=[],
        kw_defaults=[],
        kwarg=None,
        defaults=[],
    ),

    body=engine_body,

    decorator_list=[],

    returns=None,

    type_comment=None,
)


#
# Preserve already-resolved imports and local dependency
# closure definitions in their exact AST form.
#

module_body = [
    ast.ImportFrom(
        module="__future__",
        names=[
            ast.alias(
                name="annotations",
            )
        ],
        level=0,
    )
]


module_body.extend(
    copy.deepcopy(
        selected_imports
    )
)


module_body.extend(
    copy.deepcopy(
        closure_nodes
    )
)


module_body.append(
    function
)



# ============================================================
# R6-R5 EXACT DEPENDENCY CLOSURE REQUIREMENT
# ============================================================

R6_R5_REQUIRED_CLOSURE_NAMES = {
    "total_candidates",
}


def _r6_r5_target_names(node):

    names = set()

    if isinstance(node, ast.Name):

        names.add(node.id)

    elif isinstance(
        node,
        (
            ast.Tuple,
            ast.List,
        ),
    ):

        for elt in node.elts:
            names.update(
                _r6_r5_target_names(
                    elt
                )
            )

    return names


def _r6_r5_defined_names(node):

    names = set()

    for candidate in ast.walk(node):

        if isinstance(
            candidate,
            ast.Assign,
        ):

            for target in candidate.targets:
                names.update(
                    _r6_r5_target_names(
                        target
                    )
                )

        elif isinstance(
            candidate,
            ast.AnnAssign,
        ):

            names.update(
                _r6_r5_target_names(
                    candidate.target
                )
            )

    return names


_r6_r5_present_names = set()

for _r6_r5_node in (
    list(prelude_nodes)
    +
    list(selected_loop_nodes)
):

    _r6_r5_present_names.update(
        _r6_r5_defined_names(
            _r6_r5_node
        )
    )


_r6_r5_missing = (
    R6_R5_REQUIRED_CLOSURE_NAMES
    -
    _r6_r5_present_names
)


if _r6_r5_missing:

    #
    # Source only from the already-selected certified
    # R7-R1 owner function. Never execute R7-R1.
    #

    _r6_r5_candidates = []

    for _r6_r5_node in owner.body:

        _r6_r5_defs = (
            _r6_r5_defined_names(
                _r6_r5_node
            )
        )

        if (
            _r6_r5_defs
            &
            _r6_r5_missing
        ):

            _r6_r5_candidates.append(
                copy.deepcopy(
                    _r6_r5_node
                )
            )


    _r6_r5_recovered = set()

    for _r6_r5_node in (
        _r6_r5_candidates
    ):

        _r6_r5_recovered.update(
            _r6_r5_defined_names(
                _r6_r5_node
            )
        )


    _r6_r5_still_missing = (
        _r6_r5_missing
        -
        _r6_r5_recovered
    )


    if _r6_r5_still_missing:

        raise RuntimeError(
            "R6-R5 certified dependency "
            "producer missing: "
            f"{sorted(_r6_r5_still_missing)}"
        )


    #
    # Producers must precede the feature loop.
    #

    prelude_nodes.extend(
        _r6_r5_candidates
    )

# ============================================================
# END R6-R5 DEPENDENCY CLOSURE REQUIREMENT
# ============================================================

engine_module = ast.Module(
    body=module_body,
    type_ignores=[],
)


engine_module = ast.fix_missing_locations(
    engine_module
)


engine_source = (
    ast.unparse(
        engine_module
    )
    + "\n"
)


#
# This is the critical R6-R3 certification point:
# the generated feature engine itself must parse and compile.
#

engine_tree = ast.parse(
    engine_source
)


compile(
    engine_tree,
    str(
        ENGINE
    ),
    "exec",
)


#
# Structural conditional certification.
#
# We require both the numeric_identity and bm25_position
# branch structures to survive synthesis.
#

ifs = [
    node
    for node in ast.walk(
        engine_tree
    )
    if isinstance(
        node,
        ast.If
    )
]


if len(ifs) < 2:

    raise RuntimeError(
        "generated feature engine lost required conditionals"
    )


numeric_assignments = [
    node
    for node in ast.walk(
        engine_tree
    )
    if (
        isinstance(
            node,
            ast.Assign
        )
        and
        any(
            isinstance(
                target,
                ast.Name,
            )
            and
            target.id
            ==
            "numeric_identity"
            for target in node.targets
        )
    )
]


bm25_assignments = [
    node
    for node in ast.walk(
        engine_tree
    )
    if (
        isinstance(
            node,
            ast.Assign
        )
        and
        any(
            isinstance(
                target,
                ast.Name,
            )
            and
            target.id
            ==
            "bm25_position"
            for target in node.targets
        )
    )
]


if len(
    numeric_assignments
) < 2:

    raise RuntimeError(
        "numeric_identity conditional branches were not preserved"
    )


if len(
    bm25_assignments
) < 2:

    raise RuntimeError(
        "bm25_position conditional branches were not preserved"
    )


#
# Frozen score certification.
#

shadow_nodes = []


for node in ast.walk(
    engine_tree
):

    if not isinstance(
        node,
        ast.Assign
    ):
        continue

    names = set()

    for target in node.targets:

        names.update(
            target_names(
                target
            )
        )

    if "shadow_score" in names:

        shadow_nodes.append(
            node
        )


if len(
    shadow_nodes
) != 1:

    raise RuntimeError(
        "generated engine does not contain exactly one "
        "selected shadow_score producer"
    )


shadow_loaded_names = loaded_names(
    shadow_nodes[
        0
    ].value
)


expected_shadow_inputs = {
    "coverage",
    "rarity_coverage",
    "title_coverage",
    "numeric_identity",
    "bm25_position",
}


if not (
    expected_shadow_inputs
    <=
    shadow_loaded_names
):

    raise RuntimeError(
        "generated engine shadow score lost certified inputs"
    )


if (
    "full_title_identity"
    in
    shadow_loaded_names
):

    raise RuntimeError(
        "full_title_identity leaked into primary R7 score"
    )


#
# No dynamic R7-R1 harness execution may leak into engine.
#

for node in ast.walk(
    engine_tree
):

    if not isinstance(
        node,
        ast.Call
    ):
        continue

    fn = node.func

    if (
        isinstance(
            fn,
            ast.Attribute
        )
        and
        fn.attr
        ==
        "exec_module"
    ):

        raise RuntimeError(
            "exec_module leaked into generated engine"
        )


ENGINE.write_text(
    engine_source,
    encoding="utf-8",
)


#
# Store a copy under artifacts for exact inspection.
#

preview_path = Path(
    r"/media/abdullah/JARVISDATA/Projects/jarvis-ai/artifacts/genesis_recall/r4_r10_r7_r4_r1_r2_r6_r3_generated_engine_preview.py"
)

preview_path.write_text(
    engine_source,
    encoding="utf-8",
)


# ============================================================
# PATCH ONLY R7-R4 build_features()
# ============================================================

r4_source = R7R4.read_text(
    encoding="utf-8"
)

r4_tree = ast.parse(
    r4_source
)


build_matches = [
    node
    for node in r4_tree.body
    if (
        isinstance(
            node,
            (
                ast.FunctionDef,
                ast.AsyncFunctionDef,
            ),
        )
        and
        node.name
        ==
        "build_features"
    )
]


if len(
    build_matches
) != 1:

    raise RuntimeError(
        "expected exactly one R7-R4 build_features"
    )


build = build_matches[
    0
]


new_build = '''def build_features(
    query: str,
) -> list[ShadowCandidate]:

    rows = query_rows(
        query
    )

    if not rows:
        return []

    exact_rows = exact_feature_rows(
        query,
        rows,
    )

    result: list[
        ShadowCandidate
    ] = []

    for item in exact_rows:

        row = item[
            "row"
        ]

        coverage = float(
            item[
                "coverage"
            ]
        )

        rarity_coverage = float(
            item[
                "rarity_coverage"
            ]
        )

        title_coverage = float(
            item[
                "title_coverage"
            ]
        )

        numeric_identity = float(
            item[
                "numeric_identity"
            ]
        )

        full_title_identity = float(
            item[
                "full_title_identity"
            ]
        )

        bm25_position = float(
            item[
                "bm25_position"
            ]
        )

        r7_score = float(
            item[
                "r7_score"
            ]
        )

        #
        # R7-R4 EXPERIMENT:
        # BM25 position is removed from the primary score.
        #
        # Frozen R7 component values are unchanged.
        #

        r7_r4_score = (
            WEIGHTS[
                "coverage"
            ]
            * coverage

            + WEIGHTS[
                "rarity_coverage"
            ]
            * rarity_coverage

            + WEIGHTS[
                "title_coverage"
            ]
            * title_coverage

            + WEIGHTS[
                "numeric_identity"
            ]
            * numeric_identity
        )

        result.append(
            ShadowCandidate(
                document_id=
                    document_id_of(
                        row
                    ),

                chunk_id=
                    chunk_id_of(
                        row
                    ),

                title=
                    title_of(
                        row
                    ),

                production_rank=
                    int(
                        item[
                            "production_rank"
                        ]
                    ),

                coverage=
                    coverage,

                rarity_coverage=
                    rarity_coverage,

                title_coverage=
                    title_coverage,

                numeric_identity=
                    numeric_identity,

                full_title_identity=
                    full_title_identity,

                bm25_position=
                    bm25_position,

                r7_score=
                    r7_score,

                r7_r4_score=
                    r7_r4_score,
            )
        )

    return result
'''


#
# Insert exact feature engine import if absent.
#

IMPORT_LINE = (
    "from dev.recall.r4_r10_r7_exact_feature_engine "
    "import exact_feature_rows\n"
)


lines = r4_source.splitlines(
    keepends=True
)


#
# Replace build_features first, bottom-up safe.
#

lines[
    build.lineno - 1:
    build.end_lineno
] = [
    new_build
    + "\n"
]


patched = "".join(
    lines
)


if IMPORT_LINE not in patched:

    patched_tree = ast.parse(
        patched
    )

    future_nodes = [
        node
        for node in patched_tree.body
        if (
            isinstance(
                node,
                ast.ImportFrom,
            )
            and
            node.module
            ==
            "__future__"
        )
    ]

    insert_line = (
        max(
            node.end_lineno
            for node in future_nodes
        )
        + 1
        if future_nodes
        else 1
    )

    p_lines = patched.splitlines(
        keepends=True
    )

    p_lines.insert(
        insert_line - 1,
        "\n"
        + IMPORT_LINE
    )

    patched = "".join(
        p_lines
    )


patched_tree = ast.parse(
    patched
)

compile(
    patched,
    str(
        R7R4
    ),
    "exec",
)


#
# Contract: build_features may no longer call r7.<helper>.
#

new_build_nodes = [
    node
    for node in patched_tree.body
    if (
        isinstance(
            node,
            (
                ast.FunctionDef,
                ast.AsyncFunctionDef,
            ),
        )
        and
        node.name
        ==
        "build_features"
    )
]


if len(
    new_build_nodes
) != 1:

    raise RuntimeError(
        "post-patch build_features contract failed"
    )


remaining_r7_refs = sorted(
    {
        child.attr
        for child in ast.walk(
            new_build_nodes[
                0
            ]
        )
        if (
            isinstance(
                child,
                ast.Attribute,
            )
            and
            isinstance(
                child.value,
                ast.Name,
            )
            and
            child.value.id
            ==
            "r7"
        )
    }
)


if remaining_r7_refs:

    raise RuntimeError(
        "false R7 helper abstraction remains: "
        + repr(
            remaining_r7_refs
        )
    )


#
# Verify the exact R7 score remains in generated engine source.
#

#
# ============================================================
# R6-R4 FROZEN SCORE CERTIFICATION
# AST SEMANTIC EQUIVALENCE — NOT TEXT SPELLING
# ============================================================
#
# ast.unparse() normalizes numeric literals:
#     0.40 -> 0.4
#
# Therefore textual score-fragment membership is not a valid
# equivalence test.
#
# Compare the selected certified R7-R1 shadow_score expression
# against the generated engine expression structurally.
#

generated_shadow_nodes = []


for node in ast.walk(
    engine_tree
):

    if not isinstance(
        node,
        ast.Assign,
    ):
        continue

    names = set()

    for target in node.targets:

        names.update(
            target_names(
                target
            )
        )

    if "shadow_score" in names:

        generated_shadow_nodes.append(
            node
        )


if len(
    generated_shadow_nodes
) != 1:

    raise RuntimeError(
        "generated engine shadow_score producer "
        f"count invalid: {len(generated_shadow_nodes)}"
    )


generated_shadow = (
    generated_shadow_nodes[0]
)


#
# 'shadow' is the exact R5-R1-certified AST producer selected
# earlier from R7-R1.
#

certified_expr = ast.dump(
    shadow.value,
    annotate_fields=True,
    include_attributes=False,
)


generated_expr = ast.dump(
    generated_shadow.value,
    annotate_fields=True,
    include_attributes=False,
)


score_ast_equivalent = (
    certified_expr
    ==
    generated_expr
)


if not score_ast_equivalent:

    raise RuntimeError(
        "generated shadow_score AST differs from "
        "the certified R7-R1 producer\n"
        "CERTIFIED:\n"
        + certified_expr
        + "\nGENERATED:\n"
        + generated_expr
    )


#
# Also certify the input surface explicitly.
#

generated_shadow_inputs = loaded_names(
    generated_shadow.value
)


expected_shadow_inputs = {
    "coverage",
    "rarity_coverage",
    "title_coverage",
    "numeric_identity",
    "bm25_position",
}


missing_shadow_inputs = sorted(
    expected_shadow_inputs
    -
    generated_shadow_inputs
)


if missing_shadow_inputs:

    raise RuntimeError(
        "generated frozen score missing inputs: "
        + repr(
            missing_shadow_inputs
        )
    )


if (
    "full_title_identity"
    in
    generated_shadow_inputs
):

    raise RuntimeError(
        "full_title_identity leaked into "
        "the frozen R7 primary score"
    )


print(
    "frozen R7 score AST equivalence:",
    score_ast_equivalent,
)

print(
    "generated score inputs:",
    sorted(
        generated_shadow_inputs
    ),
)

print(
    "full_title_identity in score:",
    (
        "full_title_identity"
        in
        generated_shadow_inputs
    ),
)




#
# full_title_identity must not be in shadow_score expression.
#

engine_shadow = []

for node in ast.walk(
    engine_tree
):

    if not isinstance(
        node,
        ast.Assign,
    ):
        continue

    names = set()

    for target in node.targets:
        names.update(
            target_names(
                target
            )
        )

    if "shadow_score" in names:
        engine_shadow.append(
            node
        )


if len(
    engine_shadow
) != 1:

    raise RuntimeError(
        "generated engine shadow score not unique"
    )


if (
    "full_title_identity"
    in
    loaded_names(
        engine_shadow[
            0
        ].value
    )
):

    raise RuntimeError(
        "full_title_identity leaked into primary score"
    )


backup = R7R4.with_suffix(
    R7R4.suffix
    +
    ".pre_r2_r6_inline_repair"
)


if not backup.exists():

    backup.write_text(
        r4_source,
        encoding="utf-8",
    )


R7R4.write_text(
    patched,
    encoding="utf-8",
)


# ============================================================
# ARTIFACTS
# ============================================================

ENGINE_CONTRACT.write_text(
    "\n".join(
        [
            "GENESIS R2-R6 EXACT FEATURE ENGINE",
            "",
            f"R7-R1 owner function : {owner.name}",
            f"shadow_score line     : {shadow.lineno}",
            f"feature loop line     : {feature_loop.lineno}",
            "",
            "PRELUDE PRODUCERS:",
            *[
                "  "
                + segment(
                    r7_source,
                    node,
                ).replace(
                    "\n",
                    " "
                )
                for node in prelude_nodes
            ],
            "",
            "TOP-LEVEL DEPENDENCY CLOSURE:",
            *[
                "  "
                + name
                for name in sorted(
                    closure
                )
            ],
            "",
            "R7-R1 executed : NO",
            "R7-R1 modified : NO",
        ]
    )
    + "\n",
    encoding="utf-8",
)


BUILD_CONTRACT.write_text(
    "\n".join(
        [
            "GENESIS R2-R6 BUILD_FEATURES CONTRACT",
            "",
            "false r7 helper references after patch:",
            repr(
                remaining_r7_refs
            ),
            "",
            "build_features now consumes:",
            "  exact_feature_rows(query, rows)",
            "",
            "full_title_identity in primary R7 score:",
            "  NO",
            "",
            "production patch authorized:",
            "  NO",
        ]
    )
    + "\n",
    encoding="utf-8",
)


report = {
    "phase":
        "R4-R10-R7-R4-R1-R2-R6",

    "r7_r1_owner_function":
        owner.name,

    "shadow_score_line":
        shadow.lineno,

    "feature_loop_line":
        feature_loop.lineno,

    "prelude_targets":
        sorted(
            PRELUDE_TARGETS
        ),

    "dependency_closure":
        sorted(
            closure
        ),

    "remaining_r7_helper_refs":
        remaining_r7_refs,

    "engine_sha256":
        sha(
            ENGINE
        ),

    "r7_r4_sha256_after_repair":
        sha(
            R7R4
        ),

    "r7_r1_executed":
        False,

    "r7_r1_modified":
        False,

    "production_patch_authorized":
        False,

    "repair_certified":
        (
            not remaining_r7_refs
        ),
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
        [
            "GENESIS RECALL R4-R10-R7-R4-R1-R2-R6",
            "",
            "Exact R7 feature engine generated.",
            "R7-R4 build_features repaired.",
            "",
            f"R7-R1 owner function : {owner.name}",
            f"feature loop line     : {feature_loop.lineno}",
            f"shadow_score line     : {shadow.lineno}",
            "",
            "False r7 helper references remaining:",
            repr(
                remaining_r7_refs
            ),
            "",
            "R7-R1 executed : NO",
            "Production patch authorized : NO",
        ]
    )
    + "\n",
    encoding="utf-8",
)


print("=" * 78)
print(
    " GENESIS RECALL R4-R10-R7-R4-R1-R2-R6 REPAIR RESULT"
)
print("=" * 78)
print()

print(
    "R7-R1 owner function :",
    owner.name,
)

print(
    "feature loop line     :",
    feature_loop.lineno,
)

print(
    "shadow_score line     :",
    shadow.lineno,
)

print()

print(
    "prelude targets       :",
    sorted(
        PRELUDE_TARGETS
    ),
)

print(
    "dependency closure    :",
    len(
        closure
    ),
)

print()

print(
    "false R7 helper refs remaining:",
    remaining_r7_refs,
)

print()

print(
    "R7-R1 executed        : NO"
)

print(
    "R7-R1 modified        : NO"
)

print(
    "production authorized : NO"
)

print()

print(
    "R2-R6 REPAIR CERTIFIED:",
    not remaining_r7_refs,
)

print("=" * 78)


raise SystemExit(
    0
    if not remaining_r7_refs
    else 1
)
