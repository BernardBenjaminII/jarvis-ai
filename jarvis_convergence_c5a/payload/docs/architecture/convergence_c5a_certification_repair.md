# Convergence C-5A — Certification Import Repair

## Purpose

C-5A repairs the C-5 certification harness without changing the production
Executive Knowledge Awareness implementation.

## Corrected behavior

The verifier now:

- runs from the repository root;
- prepends the repository root to `PYTHONPATH`;
- invokes the C-5 test as the package-qualified module
  `tests.test_convergence_c5_executive_knowledge_awareness`;
- avoids top-level `unittest discover` imports that incorrectly load
  `tests/fixtures` as `fixtures` and C-5 tests outside the repository package
  context;
- preserves the existing structural, compilation, and orchestration checks.

## Production impact

None. C-5A changes only certification and verification files.
