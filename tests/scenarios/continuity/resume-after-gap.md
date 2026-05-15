# continuity.resume-after-gap

## Purpose

Resume a collaboration after a time gap and recover the active elephant-backed
state without requiring the user to restate the whole context.

## Setup

- one prior Episode exists with recent Loop and Step history
- the active elephant already carries `summary`, `active_task`, `next_step`, and
  `blockers`
- the conversation has been inactive long enough that the next turn should not
  rely on raw recent context alone

## Steps

1. restore the active elephant and most recent Episode continuity from durable
   records
2. inspect the latest current-work fields and recent Step facts
3. assemble a minimal context bundle from State, Record, Grounding, and Memory
   sources
4. produce the next-step recommendation

## Expected Assertions

- the same elephant is recovered
- the latest current work is visible in the resumed state
- the assistant explains why the next move is chosen now
- no duplicate or conflicting continuity packet is created

## Downstream Extensions

- `packages/kernel/**` should assert the resume lifecycle
- `packages/context/**` should prove the bundle stays small but sufficient
