# continuity.recall-recovery

## Purpose

Recover relevant recall evidence after partial context loss, deletion, or correction
without reviving stale state.

## Setup

- recall has at least one useful historical fact
- recall also contains either corrected or deprecated information
- the current turn needs the durable fact, not the stale one

## Steps

1. query the available relevant recall evidence
2. filter by current-work relevance and recency policy
3. prefer corrected facts over stale evidence
4. explain the recovered evidence to the user

## Expected Assertions

- recall retrieval is tied to the active elephant and current work
- corrected or deleted fact is not reused as truth
- recovered evidence is summarized in user-visible language
- the recovery path is stable across resumptions

## Downstream Extensions

- `packages/evidence/**` should own recall and governance rules
- `packages/context/**` should show how recovered evidence enters the bundle
- `packages/security/**` should define fact visibility and deletion policy
