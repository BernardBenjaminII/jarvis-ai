#!/usr/bin/env python3
from pathlib import Path
import textwrap

ROOT = Path(__file__).resolve().parents[2]

templates = ROOT / "docs" / "templates"
templates.mkdir(parents=True, exist_ok=True)

template = templates / "ADR_TEMPLATE.md"

template.write_text(
    textwrap.dedent(
        """\
        # ADR-####: Title

        ## Status

        Draft

        ---

        ## Context

        Why does this decision need to be made?

        ---

        ## Problem

        What problem is being solved?

        ---

        ## Decision

        Describe the chosen solution.

        ---

        ## Alternatives Considered

        - Option A
        - Option B
        - Option C

        ---

        ## Consequences

        ### Benefits

        -

        ### Costs

        -

        ### Risks

        -

        ---

        ## Migration

        How should the project transition?

        ---

        ## References

        Related ADRs:

        Architecture documents:

        Relevant source files:
        """
    ),
    encoding="utf-8",
)

print(f"Created {template}")
