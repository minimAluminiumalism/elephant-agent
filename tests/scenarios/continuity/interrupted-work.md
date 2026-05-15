# continuity.interrupted-work

## Purpose

Recover from an interrupted task without losing the active work packet or the
reason it should continue.

## Setup

- an active task has already been written into `State.active_task`
- the interruption happens before completion
- at least one pending follow-up, blocker, or tool result exists in recent Step
  facts

## Steps

1. reload the active elephant after interruption
2. inspect current-work fields and recent Step evidence
3. decide whether to continue, re-scope, or defer the task
4. explain the decision to the user

## Expected Assertions

- the interrupted task is still represented in durable state
- the current-work packet does not collapse into a fresh unrelated task
- pending blockers or follow-ups are surfaced explicitly rather than silently
  dropped
- the decision path is explainable from durable state

## Downstream Extensions

- `packages/kernel/**` should preserve active current-work fields across turns
- `packages/evidence/**` should retain the interrupted-task evidence trail
- `tests/e2e/continuity/**` should wrap the scenario in an app-level flow
