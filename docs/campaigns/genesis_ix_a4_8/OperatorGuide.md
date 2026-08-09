# Operator Guide

## Before the Run

Record the repository commit, working-tree state, environment, model, database
paths, Mission Control reachability, telemetry reachability, and run ID.

## During the Run

Submit the exact canonical prompt, capture the complete answer, qualification,
plan, final prompt, telemetry, duration, and result. Classify failures
immediately.

## Rules

- do not modify production code during a run;
- do not reinterpret expectations after seeing results;
- do not delete traces;
- do not pass a test based only on fluent wording;
- do not expose secrets in reports.
