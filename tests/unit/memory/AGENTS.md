# Memory Unit Tests

Use this directory for fast package-local tests for `packages/evidence` durable memory surfaces.

## Own Here

- ledger and extraction behavior
- consolidation and retrieval ranking
- governance and correction policy
- package surface inventory checks

## Rules

- keep tests deterministic and standard-library only
- do not depend on app processes or external storage backends
- prefer narrow fixtures that prove one memory rule at a time
