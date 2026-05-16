# recall.durable-substrate

## Purpose

Persist the Step/Episode recall evidence and Personal Model fact provenance across a full
process restart without losing correction, deletion, or retrieval behavior.

## Setup

- one SQLite database file backs the recall evidence runtime
- the first process writes multiple current-work-linked evidence
- at least one evidence item is summarized and one fact is corrected
- one corrected Personal Model fact is later deleted to verify governance survives restart

## Steps

1. bootstrap the storage repository and construct a repository-backed recall evidence runtime
2. write multiple Steps into the recall trail
3. consolidate the session to produce a durable episode summary
4. correct a stale evidence and verify the replacement relationship is recorded
5. restart the process by constructing a new runtime from the same database file
6. retrieve recall evidence for the active current-work item after the restart
7. delete the corrected Personal Model fact and restart again to confirm the deletion state persists

## Expected Assertions

- the ledger survives restart and still lists all appended events
- consolidated evidence remains marked consolidated after restart
- corrected Personal Model fact remains linked to its replacement summary or correction target
- deleted fact stays deleted after restart and no longer appears in retrieval
- retrieval still ranks the durable, current-work-linked truth ahead of stale state

## Downstream Extensions

- `packages/evidence/**` and `packages/semantic_index/**` should own the recall evidence runtime and lineage rules
- `packages/storage/**` should persist the ledger and State baseline
- `tests/e2e/continuity/**` should reuse this fixture to prove restart behavior in app flows
