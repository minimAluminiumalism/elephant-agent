# recall.resume-after-gap

## Purpose

Resume a collaboration after a time gap and recover the relevant recall evidence that
still matters to the active current-work item.

## Setup

- a prior session contains current-work-linked Step records
- the session has been inactive long enough that the current turn should not
  rely on short-term context alone
- one fact has been corrected so the retriever must prefer the current truth

## Steps

1. query the Step/Episode recall trail for the active session
2. retrieve current-work-linked evidence with recency and correction awareness
3. surface the highest-value relevant recall evidence to the user
4. explain why that evidence is still relevant now

## Expected Assertions

- current-work-linked evidence remain retrievable after inactivity
- corrected Personal Model fact is preferred over stale evidence
- the recovery explanation references durable state instead of prompt noise
- the retrieval path is stable across resumptions

## Downstream Extensions

- `packages/evidence/**` and `packages/semantic_index/**` should own the retrieval and governance rules
- `packages/kernel/**` should pass active current-work ids into retrieval
- `tests/e2e/continuity/**` should prove the recall evidence survives a real app flow
