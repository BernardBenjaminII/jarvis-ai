# Genesis IX-A4.3C Pack 3A.2 — AST Reconstruction Repair

Repairs bound-method AST parsing by routing source analysis through
`core/runtime/source_analysis.py`.

The canonical source-analysis service uses `inspect.unwrap()` and
`textwrap.dedent()` before `ast.parse()`. It returns structured states instead
of aborting when source is unavailable or unparseable.

Regression coverage includes bound instance methods, class methods, static
methods, decorated methods, nested functions, indented source, dedented source,
malformed source, and compiled callables.

After repair, IX-A4.3C is rerun and must generate its full report set.
