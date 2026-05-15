# Continuity Fixtures

This directory seeds the continuity-evaluation vocabulary for Elephant Agent.

Track goals:

- resume after a time gap
- recover current work from durable state after interruption
- recover memory after partial context loss
- explain the next move in a way that survives handoff
- keep canonical identity and relationship continuity stable across turns
- keep re-engagement guidance user-governed instead of hiding it behind
  deleted planner internals
- keep correction-aware recovery from reviving superseded or deleted evidence
- keep refocus recovery centered on active work even when nearby scope is noisy
- keep continuity text-first and surface-owned without a parallel audio contract

File conventions:

- one scenario per file
- stable scenario ID at the top of each file
- explicit setup, steps, and assertions
- extensions should add new scenarios instead of mutating historical meaning

Canonical downstream consumers:

- `tests/e2e/continuity/**`
- `packages/kernel/**`
- `packages/context/**`
- `packages/evidence/**`
- `apps/cli/**`
- `apps/gateway/**`
