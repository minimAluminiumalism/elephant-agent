# memory.correction-and-deletion

## Purpose

Correct stale memory, delete disallowed memory, and keep the durable trail
inspectable.

## Setup

- memory contains one stale fact and one protected fact
- the active session needs the corrected fact, not the stale one
- the protected fact should not be deleted by an unprivileged actor

## Steps

1. issue a correction for the stale memory
2. attempt to delete the protected memory through governance
3. retrieve memory for the active current-work item after the correction
4. inspect the durable trail to confirm supersession and deletion state

## Expected Assertions

- corrections supersede stale memory instead of rewriting history
- protected memory is not deleted without explicit governance permission
- retrieval ignores deleted or superseded records
- the resulting trail remains inspectable and explainable

## Downstream Extensions

- `packages/memory/**` should own the correction and deletion entrypoints
- `packages/security/**` should later refine visibility and deletion policy
- `tests/e2e/continuity/**` should prove corrections survive an app restart
