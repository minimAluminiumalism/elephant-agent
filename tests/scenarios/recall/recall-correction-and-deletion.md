# recall.correction-and-deletion

## Purpose

Correct stale evidence, delete disallowed facts, and keep the durable trail
inspectable.

## Setup

- recall has one stale fact and one protected fact
- the active session needs the corrected fact, not the stale one
- the protected fact should not be deleted by an unprivileged actor

## Steps

1. issue a correction for the stale evidence
2. attempt to delete the protected fact through governance
3. retrieve recall evidence for the active current-work item after the correction
4. inspect the durable trail to confirm supersession and deletion state

## Expected Assertions

- corrections supersede stale evidence instead of rewriting history
- protected fact is not deleted without explicit governance permission
- retrieval ignores deleted or superseded records
- the resulting trail remains inspectable and explainable

## Downstream Extensions

- `packages/evidence/**` and `packages/semantic_index/**` should own the correction and deletion entrypoints
- `packages/security/**` should later refine visibility and deletion policy
- `tests/e2e/continuity/**` should prove corrections survive an app restart
