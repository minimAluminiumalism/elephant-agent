# continuity.explainable-next-step

## Purpose

Prove that the system can justify the next move instead of only emitting an
instruction.

## Setup

- the active elephant has durable current-work fields and at least one viable next
  action
- competing actions are possible so the choice matters

## Steps

1. inspect current-work fields, recent Step facts, and relevant memory
2. rank the next possible actions
3. select the preferred move
4. surface the rationale in plain language

## Expected Assertions

- the next step has a visible explanation
- the explanation references durable elephant, Step, or Memory state
- the explanation is not a generic prompt artifact
- the rationale remains meaningful after a restart

## Downstream Extensions

- `packages/kernel/**` should preserve the chosen move and its reason
- `tests/e2e/continuity/**` should verify the explanation survives an app flow
