# Memory Fixtures

This directory seeds the recall-evaluation vocabulary for Elephant Agent.

Track goals:

- recover recall evidence after a long gap
- prefer corrected Personal Model fact over stale evidence
- explain why a recovered evidence is still relevant
- keep recall and Personal Model governance inspectable
- survive restart without flattening lineage or correction state

File conventions:

- one scenario per file
- stable scenario ID at the top of each file
- explicit setup, steps, and assertions
- extensions should add new scenarios instead of mutating historical meaning

Canonical downstream consumers:

- `packages/evidence/**` and `packages/semantic_index/**`
- `packages/kernel/**`
- `tests/e2e/continuity/**`
