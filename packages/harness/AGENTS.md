# Harness

Long-horizon harness subsystems. Owns the runtime behaviours that make a
single task survive 24h+ unattended:

* **Retry policy** (`retry_policy.py`) — generic exponential-backoff wrapper
  that honours `Retry-After`, classifies errors into retryable vs permanent,
  and threads `RetryState` / idempotency keys back into `LoopState` so
  resume replays reuse the same semantics.
* **Wait conditions** — parsing / serialisation of `WaitCondition` records
  carried by `LoopState`. Concrete subsystems (supervisor, event bus,
  network probe) land alongside this package in later commits.

Design reference: `docs/system-design/system-layer-model.md` §Loop /
§Runtime Flow; master plan `~/.claude-internal/plans/long-horizon-harness.md`.

## Dependency direction

`packages/harness` depends on `packages/contracts` and `packages/storage`
only. It is callable from `packages/kernel` and `packages/models/providers`.
Apps (`apps/supervisor_command.py`, `apps/learning_worker_runtime.py`)
consume the harness; the harness never imports from `apps/`.

## No backward compatibility shims

Per `CLAUDE.md`, every change to a contract or API lands in one commit
with all call sites updated. This package is part of the Phase 1 plan
(`~/.claude-internal/plans/toasty-launching-robin.md`) and will grow with
Phases 2–5.
