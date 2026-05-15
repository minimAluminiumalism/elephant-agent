# Project Guidelines

## Development Stage

This repository is in **active, pre-release development** and is not yet open-sourced.
Iteration speed and code quality outrank compatibility. Every change should leave the
codebase **up to date, clean, and high quality** — even if that means deleting or
rewriting code that is already there.

## No Backward Compatibility

Do not consider backward compatibility in any change. There are no shipped consumers
to protect. If a better shape requires changing a public type, interface, schema, on-disk
layout, CLI flag, config key, or API contract, change it — and update every call site
in the same commit. Never add deprecation shims, feature flags to keep old behaviour,
or "legacy" fallback branches.

## Critical Review of Existing Code

This project has been redesigned multiple times. **Do not assume existing code is
correct or represents the intended architecture.** Patterns you find in the tree may
be leftover from an earlier design and may actively conflict with the current one.

When taking on any task:

1. Read the authoritative system design at `docs/system-design/system-layer-model.md`
   and verify your change aligns with it — not with the surrounding code.
2. Treat unfamiliar code as a **hypothesis to be tested**, not as ground truth. Ask:
   does this actually match the current design? Is it the simplest shape? Is it still
   used? Could it be deleted outright?
3. If existing code is legacy, rewrite or remove it as part of the task. Leaving
   mismatched code in place is a quality regression even when the immediate task
   would technically work around it.
4. Prefer the smallest, most direct implementation. Duplication, dead branches,
   unreachable fallbacks, and "just in case" abstractions are bugs — remove them.

Every task is a chance to raise the baseline. Implement it **dialectically**: verify
the premise, challenge the surrounding context, and leave the touched area better
than you found it.

## Code Cleanliness

The code must match the current system design. The authoritative system design is at:
`docs/system-design/system-layer-model.md`.

Legacy code that doesn't align with the current system design should be identified
and cleaned up, not preserved.

## Architecture Principles

- **apps → packages single-direction dependency**: apps depend on packages, never on each other. Apps are thin shells that can be replaced without rewriting the kernel.
- **Inter-package communication**: packages integrate through `packages/contracts/` and `packages/capabilities/`. Never reach into another package's private internals.
- **contracts package**: dependency-light, side-effect-free. Owns shared records, schemas, IDs, error codes. No runtime orchestration here.
- **kernel package**: owns the canonical runtime lifecycle — Record ingestion, State resolution, Episode/Loop/Step orchestration, Grounding, persistence, reflection triggers.
- **Shared behavior goes up**: when an app needs shared behavior, move it into `packages/`.

## Git Workflow

- Use Conventional Commits: `<type>(<scope>): <summary>`.
- Keep commits atomic: one behavior change per commit.
- **Commit and push automatically.** When a task is complete and tests pass, commit
  the change and run `git push origin main` immediately. Do not wait for user
  confirmation to commit or push — that is the default behaviour, not an opt-in.
- The only exceptions: (a) the change is still in progress / tests are red, or
  (b) the user explicitly tells you not to commit.
- Never run destructive git commands (`reset --hard`, `push --force`, etc.) without
  an explicit user instruction.

## Document Output

- Analysis and execution plans → `docs/agent/plans/`
- Architecture decisions → `docs/agent/adr/`
- Task cards → `docs/agent/task-cards/`
- Never dump generated documents in the project root.

## Useful Commands

- `make agent-validate` — run validation
- `make agent-lint` — lint check
- `make agent-test` — run tests
- `make agent-fast-gate` — quick pre-commit gate
