# memory.durable-memory-substrate

## Purpose

Persist the memory ledger, memory records, and lineage state across a full
process restart without losing correction, deletion, or retrieval behavior.

## Setup

- one SQLite database file backs the memory runtime
- the first process writes multiple current-work-linked memories
- at least one memory is consolidated and one memory is corrected
- one corrected memory is later deleted to verify governance survives restart

## Steps

1. bootstrap the storage repository and construct a repository-backed memory runtime
2. append multiple events into the memory ledger
3. consolidate the session to produce a durable summary memory
4. correct a stale memory and verify the replacement relationship is recorded
5. restart the process by constructing a new runtime from the same database file
6. retrieve memory for the active current-work item after the restart
7. delete the corrected memory and restart again to confirm the deletion state persists

## Expected Assertions

- the ledger survives restart and still lists all appended events
- consolidated memories remain marked consolidated after restart
- corrected memory remains linked to its replacement summary or correction target
- deleted memory stays deleted after restart and no longer appears in retrieval
- retrieval still ranks the durable, current-work-linked truth ahead of stale state

## Downstream Extensions

- `packages/memory/**` should own the durable memory runtime and lineage rules
- `packages/storage/**` should persist the ledger and record state baseline
- `tests/e2e/continuity/**` should reuse this fixture to prove restart behavior in app flows
