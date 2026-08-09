# Acceptance Criteria

A fluent answer without qualified support does not pass.

## Mandatory Assertions

- the public conversation request completes;
- relevant evidence is retrieved for known queries;
- irrelevant evidence remains rejected;
- unsupported questions create explicit gaps;
- the original operator request reaches the final prompt;
- grounding and grounded-answer sections reach synthesis;
- synthesis executes exactly once;
- telemetry matches qualification and planning state;
- Mission Control reflects the API projection;
- dependency failure degrades explicitly without fabrication.

## Automatic Failure Conditions

- fabricated evidence or citations;
- unsupported material classified as known;
- telemetry contradicting the runtime trace;
- unhandled exception reaching the operator;
- final prompt omitting the operator request;
- synthesis executing more than once.
