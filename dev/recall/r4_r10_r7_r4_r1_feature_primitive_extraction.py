from __future__ import annotations

import ast
import csv
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

OUTDIR = (
    PROJECT
    / "artifacts/genesis_recall"
)

REPORT = (
    OUTDIR
    / "r4_r10_r7_r4_r1_feature_primitive_extraction.json"
)

SOURCE_OUT = (
    OUTDIR
    / "r4_r10_r7_r4_r1_feature_primitive_source.txt"
)

CLOSURE_OUT = (
    OUTDIR
    / "r4_r10_r7_r4_r1_dependency_closure.tsv"
)

TRACE_OUT = (
    OUTDIR
    / "r4_r10_r7_r4_r1_isolation_trace.txt"
)


REQUIRED_PRIMITIVES = (
    "tokenize_query",
    "token_set_for_candidate",
    "query_token_rarity",
    "coverage_score",
    "rarity_coverage_score",
    "title_coverage_score",
    "numeric_identity_score",
    "full_title_identity_score",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(
        path.read_bytes()
    ).hexdigest()


def names_loaded(node: ast.AST) -> set[str]:

    values: set[str] = set()

    for child in ast.walk(node):

        if (
            isinstance(child, ast.Name)
            and isinstance(child.ctx, ast.Load)
        ):
            values.add(child.id)

    return values


def names_defined(node: ast.AST) -> set[str]:

    values: set[str] = set()

    if isinstance(
        node,
        (
            ast.FunctionDef,
            ast.AsyncFunctionDef,
            ast.ClassDef,
        ),
    ):
        values.add(node.name)

    elif isinstance(node, ast.Assign):

        for target in node.targets:

            if isinstance(target, ast.Name):
                values.add(target.id)

    elif isinstance(node, ast.AnnAssign):

        if isinstance(node.target, ast.Name):
            values.add(node.target.id)

    return values


def source_segment(
    source: str,
    node: ast.AST,
) -> str:

    segment = ast.get_source_segment(
        source,
        node,
    )

    if segment is None:
        raise RuntimeError(
            f"cannot extract source at line "
            f"{getattr(node, 'lineno', '?')}"
        )

    return segment


r7_source = R7R1.read_text(
    encoding="utf-8"
)

r7_tree = ast.parse(
    r7_source
)


# ------------------------------------------------------------
# Build top-level definition index.
# ------------------------------------------------------------

definitions: dict[str, ast.AST] = {}

imports: list[ast.AST] = []

for node in r7_tree.body:

    if isinstance(
        node,
        (
            ast.Import,
            ast.ImportFrom,
        ),
    ):
        imports.append(node)
        continue

    for name in names_defined(node):

        if name in definitions:
            raise RuntimeError(
                f"duplicate top-level definition: {name}"
            )

        definitions[name] = node


missing = [
    name
    for name in REQUIRED_PRIMITIVES
    if name not in definitions
]

if missing:
    raise RuntimeError(
        "required R7 primitives missing: "
        + ", ".join(missing)
    )


# ------------------------------------------------------------
# Dependency closure.
#
# Only follow names that resolve to top-level definitions
# inside the R7-R1 source.
#
# Imported modules/functions are handled separately by
# retaining the original import statements.
# ------------------------------------------------------------

required: set[str] = set(
    REQUIRED_PRIMITIVES
)

frontier = list(
    REQUIRED_PRIMITIVES
)

dependency_edges: list[
    tuple[str, str]
] = []


while frontier:

    current = frontier.pop(0)

    node = definitions[current]

    for loaded in sorted(
        names_loaded(node)
    ):

        if loaded not in definitions:
            continue

        dependency_edges.append(
            (
                current,
                loaded,
            )
        )

        if loaded in required:
            continue

        required.add(loaded)
        frontier.append(loaded)


# ------------------------------------------------------------
# Preserve source ordering.
# ------------------------------------------------------------

selected_nodes: list[ast.AST] = []

seen_node_ids: set[int] = set()

for node in r7_tree.body:

    node_names = names_defined(node)

    if not (
        node_names
        & required
    ):
        continue

    if id(node) in seen_node_ids:
        continue

    selected_nodes.append(node)
    seen_node_ids.add(id(node))


# ------------------------------------------------------------
# Import filtering.
#
# Start with original imports, but only retain imports whose
# bound names are actually referenced by selected definitions.
# ------------------------------------------------------------

selected_loaded: set[str] = set()

for node in selected_nodes:
    selected_loaded.update(
        names_loaded(node)
    )


def import_bound_names(
    node: ast.AST,
) -> set[str]:

    result: set[str] = set()

    if isinstance(node, ast.Import):

        for alias in node.names:

            if alias.asname:
                result.add(alias.asname)
            else:
                result.add(
                    alias.name.split(".")[0]
                )

    elif isinstance(node, ast.ImportFrom):

        for alias in node.names:

            if alias.name == "*":
                continue

            result.add(
                alias.asname
                or alias.name
            )

    return result


selected_imports: list[ast.AST] = []

for node in imports:

    bound = import_bound_names(node)

    if bound & selected_loaded:
        selected_imports.append(node)


# ------------------------------------------------------------
# Construct isolated primitive source.
# ------------------------------------------------------------

parts: list[str] = [
    "from __future__ import annotations",
    "",
]

for node in selected_imports:

    segment = source_segment(
        r7_source,
        node,
    )

    if segment.strip() == (
        "from __future__ import annotations"
    ):
        continue

    parts.append(segment)
    parts.append("")


for node in selected_nodes:

    parts.append(
        source_segment(
            r7_source,
            node,
        )
    )

    parts.append("")


primitive_source = (
    "\n".join(parts).rstrip()
    + "\n"
)


# ------------------------------------------------------------
# Critical isolation safety.
# ------------------------------------------------------------

primitive_tree = ast.parse(
    primitive_source
)

for node in primitive_tree.body:

    if isinstance(
        node,
        ast.If,
    ):

        test_text = ast.unparse(
            node.test
        )

        if "__name__" in test_text:
            raise RuntimeError(
                "executable main guard leaked into "
                "primitive source"
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
        isinstance(fn, ast.Attribute)
        and fn.attr == "exec_module"
    ):
        raise RuntimeError(
            "exec_module leaked into "
            "primitive source"
        )


# No top-level calls other than benign definition-time
# expressions are allowed.
#
# Specifically forbid common certification/runtime actions.

FORBIDDEN_TOP_LEVEL_NAMES = {
    "main",
    "run",
    "connect",
    "exit",
    "quit",
}

FORBIDDEN_TOP_LEVEL_ATTRS = {
    "exec_module",
    "connect",
    "write_text",
    "write_bytes",
    "unlink",
    "replace",
    "rename",
}


def calls_in_statement(
    node: ast.AST,
) -> list[ast.Call]:

    return [
        child
        for child in ast.walk(node)
        if isinstance(child, ast.Call)
    ]


for node in primitive_tree.body:

    if isinstance(
        node,
        (
            ast.FunctionDef,
            ast.AsyncFunctionDef,
            ast.ClassDef,
            ast.Import,
            ast.ImportFrom,
        ),
    ):
        continue

    for call in calls_in_statement(
        node
    ):

        fn = call.func

        if (
            isinstance(fn, ast.Name)
            and fn.id
            in FORBIDDEN_TOP_LEVEL_NAMES
        ):
            raise RuntimeError(
                "forbidden top-level call: "
                + fn.id
            )

        if (
            isinstance(fn, ast.Attribute)
            and fn.attr
            in FORBIDDEN_TOP_LEVEL_ATTRS
        ):
            raise RuntimeError(
                "forbidden top-level call: "
                + fn.attr
            )


# ------------------------------------------------------------
# Compile the isolated source WITHOUT executing it.
# ------------------------------------------------------------

compile(
    primitive_source,
    str(SOURCE_OUT),
    "exec",
)


# ------------------------------------------------------------
# Write extraction artifacts.
# ------------------------------------------------------------

SOURCE_OUT.write_text(
    primitive_source,
    encoding="utf-8",
)


with CLOSURE_OUT.open(
    "w",
    encoding="utf-8",
    newline="",
) as handle:

    writer = csv.writer(
        handle,
        delimiter="\t",
    )

    writer.writerow(
        (
            "parent",
            "dependency",
        )
    )

    for parent, dependency in sorted(
        set(dependency_edges)
    ):
        writer.writerow(
            (
                parent,
                dependency,
            )
        )


trace_lines = [
    "GENESIS RECALL R4-R10-R7-R4-R1",
    "",
    "R7-R1 source:",
    str(R7R1),
    "",
    "R7-R4 source:",
    str(R7R4),
    "",
    "Required primitives:",
]

for name in REQUIRED_PRIMITIVES:
    trace_lines.append(
        f"  {name}"
    )

trace_lines.extend(
    (
        "",
        "Dependency closure:",
    )
)

for name in sorted(required):
    trace_lines.append(
        f"  {name}"
    )

trace_lines.extend(
    (
        "",
        "Selected imports:",
    )
)

for node in selected_imports:
    trace_lines.append(
        "  "
        + source_segment(
            r7_source,
            node,
        ).replace(
            "\n",
            " ",
        )
    )

trace_lines.extend(
    (
        "",
        "ISOLATION:",
        "  R7-R1 imported      : NO",
        "  R7-R1 executed      : NO",
        "  primitive AST parsed: YES",
        "  primitive compiled  : YES",
        "  exec_module present : NO",
        "  production writes   : NO",
    )
)

TRACE_OUT.write_text(
    "\n".join(trace_lines)
    + "\n",
    encoding="utf-8",
)


report: dict[str, Any] = {
    "phase":
        "R4-R10-R7-R4-R1",

    "purpose":
        (
            "Extract exact R7 feature primitives "
            "without executing R7-R1"
        ),

    "r7_r1_sha256":
        sha256(R7R1),

    "r7_r4_sha256_before_repair":
        sha256(R7R4),

    "required_primitives":
        list(REQUIRED_PRIMITIVES),

    "required_primitive_count":
        len(REQUIRED_PRIMITIVES),

    "resolved_primitives":
        [
            name
            for name in REQUIRED_PRIMITIVES
            if name in definitions
        ],

    "dependency_closure":
        sorted(required),

    "dependency_closure_count":
        len(required),

    "selected_import_count":
        len(selected_imports),

    "r7_r1_imported":
        False,

    "r7_r1_executed":
        False,

    "primitive_source_compiles":
        True,

    "exec_module_in_primitive_source":
        False,

    "diagnostic_certified":
        True,
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


# ------------------------------------------------------------
# Repair R7-R4 import architecture.
#
# Replace the dynamic R7-R1 module execution with execution
# of the isolated primitive source.
#
# This is a diagnostic-harness-only repair.
# ------------------------------------------------------------

r7r4_source = R7R4.read_text(
    encoding="utf-8"
)

r7r4_tree = ast.parse(
    r7r4_source
)


exec_calls: list[ast.Call] = []

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
        isinstance(fn, ast.Attribute)
        and fn.attr == "exec_module"
    ):
        exec_calls.append(node)


if len(exec_calls) != 1:
    raise RuntimeError(
        "expected exactly one R7-R4 "
        "exec_module call, found "
        f"{len(exec_calls)}"
    )


exec_call = exec_calls[0]


# Find enclosing top-level statement.
target_statement = None

for node in r7r4_tree.body:

    if (
        getattr(node, "lineno", 0)
        <= exec_call.lineno
        <= getattr(
            node,
            "end_lineno",
            exec_call.lineno,
        )
    ):
        target_statement = node
        break


if target_statement is None:
    raise RuntimeError(
        "could not resolve exec_module "
        "top-level statement"
    )


lines = r7r4_source.splitlines(
    keepends=True
)

start = target_statement.lineno - 1
end = target_statement.end_lineno


indent = ""

original_segment = "".join(
    lines[start:end]
)


# Preserve the existing module namespace object expected by
# the remainder of R7-R4, but populate it only from the
# isolated primitive source.
#
# We deliberately do not import R7-R1.

replacement = (
    "# R7-R4-R1 DIAGNOSTIC ISOLATION REPAIR\n"
    "# Do not import/execute the R7-R1 certification harness.\n"
    "R7_PRIMITIVE_SOURCE = Path(\n"
    "    '/media/abdullah/JARVISDATA/Projects/jarvis-ai/"
    "artifacts/genesis_recall/"
    "r4_r10_r7_r4_r1_feature_primitive_source.txt'\n"
    ")\n"
    "\n"
    "if not R7_PRIMITIVE_SOURCE.is_file():\n"
    "    raise RuntimeError(\n"
    "        'R7-R4-R1 primitive source missing'\n"
    "    )\n"
    "\n"
    "exec(\n"
    "    compile(\n"
    "        R7_PRIMITIVE_SOURCE.read_text(encoding='utf-8'),\n"
    "        str(R7_PRIMITIVE_SOURCE),\n"
    "        'exec',\n"
    "    ),\n"
    "    r7.__dict__,\n"
    ")\n"
)


# Ensure Path is already available in R7-R4.
path_available = False

for node in r7r4_tree.body:

    if isinstance(
        node,
        ast.ImportFrom,
    ) and node.module == "pathlib":

        for alias in node.names:

            if (
                alias.name == "Path"
                or alias.asname == "Path"
            ):
                path_available = True


if not path_available:
    replacement = (
        "from pathlib import Path\n"
        + replacement
    )


lines[start:end] = [
    replacement
]


repaired = "".join(lines)


# Validate that the dynamic module execution is gone.

repaired_tree = ast.parse(
    repaired
)

remaining_exec_module = []

for node in ast.walk(
    repaired_tree
):

    if not isinstance(
        node,
        ast.Call,
    ):
        continue

    fn = node.func

    if (
        isinstance(fn, ast.Attribute)
        and fn.attr == "exec_module"
    ):
        remaining_exec_module.append(
            node.lineno
        )


if remaining_exec_module:
    raise RuntimeError(
        "exec_module remains after repair: "
        + repr(
            remaining_exec_module
        )
    )


# The R7-R4 experiment itself must remain present.

required_experiment_markers = (
    "bm25",
    "79286",
)

lower_repaired = repaired.casefold()

for marker in required_experiment_markers:

    if marker not in lower_repaired:
        raise RuntimeError(
            "R7-R4 experiment marker "
            f"missing after repair: {marker}"
        )


backup = R7R4.with_suffix(
    R7R4.suffix
    + ".pre_r4_r1_isolation"
)

if not backup.exists():
    backup.write_text(
        r7r4_source,
        encoding="utf-8",
    )


R7R4.write_text(
    repaired,
    encoding="utf-8",
)


# Compile repaired R7-R4.

compile(
    repaired,
    str(R7R4),
    "exec",
)


print(
    "=" * 78
)

print(
    " GENESIS RECALL R4-R10-R7-R4-R1 RESULT"
)

print(
    "=" * 78
)

print()

print(
    "R7 FEATURE PRIMITIVES"
)

print(
    "  required                  :",
    len(REQUIRED_PRIMITIVES),
)

print(
    "  resolved                  :",
    len(
        report[
            "resolved_primitives"
        ]
    ),
)

print(
    "  dependency closure        :",
    len(required),
)

print()

print(
    "ISOLATION"
)

print(
    "  R7-R1 imported            : NO"
)

print(
    "  R7-R1 executed            : NO"
)

print(
    "  exec_module after repair  :",
    len(
        remaining_exec_module
    ),
)

print(
    "  primitive source compile  : PASS"
)

print(
    "  repaired R7-R4 compile    : PASS"
)

print()

print(
    "R4-R10-R7-R4-R1 DIAGNOSTIC CERTIFIED : True"
)

print()

print(
    "Report :",
    REPORT,
)

print(
    "Source :",
    SOURCE_OUT,
)

print(
    "Closure:",
    CLOSURE_OUT,
)

print(
    "Trace  :",
    TRACE_OUT,
)

print(
    "=" * 78
)
