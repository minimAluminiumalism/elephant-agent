# Kernel Package

This package owns the canonical runtime lifecycle.

## Own Here

- source event ingestion orchestration
- default `PersonalModel` and active elephant `State` resolution
- `Episode`, `Loop`, and `Step` orchestration
- Step and Fact provenance wiring for durable writes
- calls into context, memory, semantic index, reflection, tool, and capability layers
- post-action persistence, reflection triggers, and telemetry hooks

## Do Not Own Here

- provider-specific logic
- delivery adapter specifics
- direct storage implementation details
- deleted product-facing reset-era system-layer terms or legacy planning
  semantics
