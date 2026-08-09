# Test Methodology

```text
Test definition
    ↓
Precondition verification
    ↓
Operator request
    ↓
Runtime execution
    ↓
Trace and telemetry capture
    ↓
Expected-versus-observed comparison
    ↓
Failure classification
    ↓
Subsystem scoring
    ↓
Evidence archival
```

Each test record must contain the test ID, run ID, timestamp, operator input,
expected behavior, observed answer, qualification state, evidence counts,
confidence, citations, conflicts, telemetry, duration, result, classification,
and artifact paths.

Test classes include positive, negative, boundary, recovery, repeatability, and
performance tests.
