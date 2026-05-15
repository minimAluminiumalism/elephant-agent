# memory.resume-after-gap

## Purpose

Resume a collaboration after a time gap and recover the durable memory that
still matters to the active current-work item.

## Setup

- a prior session contains current-work-linked memory records
- the session has been inactive long enough that the current turn should not
  rely on short-term context alone
- one memory has been corrected so the retriever must prefer the current truth

## Steps

1. query the memory ledger for the active session
2. retrieve current-work-linked memories with recency and correction awareness
3. surface the highest-value durable memory to the user
4. explain why that memory is still relevant now

## Expected Assertions

- current-work-linked memories remain retrievable after inactivity
- corrected memory is preferred over stale memory
- the recovery explanation references durable state instead of prompt noise
- the retrieval path is stable across resumptions

## Downstream Extensions

- `packages/memory/**` should own the retrieval and governance rules
- `packages/kernel/**` should pass active current-work ids into retrieval
- `tests/e2e/continuity/**` should prove the memory survives a real app flow
