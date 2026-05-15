# Architecture Guardrails

## General Rules

- keep the root thin; new logic should land under `apps/`, `packages/`, `tests/`, or `tools/agent/`
- keep product-facing design drafts under `docs/system-design/` and harness policy under `docs/agent/`
- do not mix harness orchestration with product logic
- prefer small orchestrators plus narrow helpers over large multi-purpose files
- add a local `AGENTS.md` before a subdirectory accumulates non-obvious invariants

## Current Ratchets

- harness files should stay readable enough that a new contributor can audit them in one sitting
- CI should call canonical make targets instead of reimplementing logic inline
- commit guardrails and worktree guardrails should remain executable, not prose-only
