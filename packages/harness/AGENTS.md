# Harness Package

This package owns long-horizon runtime support primitives.

## Own Here

- retry policy and `RetryState` handling
- supervisor heartbeat, crash-scan, and timer-wake loops
- wait-condition support around parked `LoopState` records
- storage-facing protocols used by the supervisor

## Do Not Own Here

- app command rendering
- model-provider adapter logic
- storage schema implementation
- kernel turn execution

## Dependency Direction

`packages/harness` may depend on `packages/contracts` and storage-facing
interfaces. It is callable from kernel and app process wiring, but it must not
import from `apps/`.

Use `docs/system-design/system-layer-model.md` as the durable design reference
for Loop, WaitCondition, and runtime-flow semantics.
