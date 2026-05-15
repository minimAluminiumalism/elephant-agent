# continuity.memory-recovery

## Purpose

Recover relevant memory after partial context loss, deletion, or correction
without reviving stale state.

## Setup

- memory contains at least one useful historical fact
- memory also contains either corrected or deprecated information
- the current turn needs the durable fact, not the stale one

## Steps

1. query the available durable memory
2. filter by current-work relevance and recency policy
3. prefer corrected memory over stale memory
4. explain the recovered memory to the user

## Expected Assertions

- memory retrieval is tied to the active elephant and current work
- corrected or deleted memory is not reused as truth
- recovered memory is summarized in user-visible language
- the recovery path is stable across resumptions

## Downstream Extensions

- `packages/evidence/**` should own recall and governance rules
- `packages/context/**` should show how recovered memory enters the bundle
- `packages/security/**` should define memory visibility and deletion policy
