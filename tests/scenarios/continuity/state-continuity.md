# continuity.state-continuity

## Purpose

Keep canonical identity and relationship continuity stable across turns.

## Setup

- a profile defines the durable identity posture that seeds canonical state
- the conversation has prior relational context
- the user returns after a gap or interruption

## Steps

1. reload the profile and canonical state owners
2. restore the identity settings that shape the mode and initiative
3. continue the conversation through a text-only surface
4. project continuity from canonical identity, user, and relationship records
5. keep the delivery boundary outside the identity model

## Expected Assertions

- identity configuration persists across resumes
- continuity projection stays aligned with canonical state owners
- relationship continuity remains visible to the user
- no voice transport or speech-specific prompt contract is needed to preserve continuity

## Downstream Extensions

- `packages/profile/**` should own profile bootstrap inputs only
- `packages/personal_state/**` should own canonical identity and user projection helpers
- `packages/continuity/**` should project resumable continuity from canonical records
- `apps/gateway/**` should keep continuity text-first without a parallel voice path
