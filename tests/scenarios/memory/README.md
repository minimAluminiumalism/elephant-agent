# Memory Fixtures

This directory seeds the memory-evaluation vocabulary for Elephant Agent.

Track goals:

- recover memory after a long gap
- prefer corrected memory over stale memory
- explain why a recovered memory is still relevant
- keep memory governance inspectable
- survive restart without flattening lineage or correction state

File conventions:

- one scenario per file
- stable scenario ID at the top of each file
- explicit setup, steps, and assertions
- extensions should add new scenarios instead of mutating historical meaning

Canonical downstream consumers:

- `packages/memory/**`
- `packages/kernel/**`
- `tests/e2e/continuity/**`
