# Telemetry Package

`packages/telemetry` defines the backend-neutral event contract used by the
kernel and enforcement tracks.

## Event Families

- `lifecycle`: turn ingestion, session recovery, context assembly, persistence,
  and emission checkpoints
- `execution`: model requests, tool calls, side effects, and reply generation
- `approval`: policy classification, decisions, grants, denials, and deferrals
- `delivery`: surface delivery, acknowledgements, and channel failures
- `failure`: runtime errors, side-effect faults, and other auditable failures

## Public Contract

- `TelemetryMetadata`
- `LifecycleTelemetryEvent`
- `ExecutionTelemetryEvent`
- `ApprovalTelemetryEvent`
- `DeliveryTelemetryEvent`
- `FailureTelemetryEvent`
- `TelemetrySink`
- `emit_event`
- `emit_lifecycle_event`
- `emit_execution_event`
- `emit_approval_event`
- `emit_delivery_event`
- `emit_failure_event`

## Required Emission Coverage

`KRN-1` must emit the lifecycle and execution checkpoints that describe the
canonical turn path:

- `lifecycle.turn.ingested`
- `lifecycle.session.resolved`
- `lifecycle.state.recovered`
- `lifecycle.context.assembled`
- `execution.move.selected`
- `execution.tool.requested`
- `execution.reply.emitted`
- `lifecycle.outcomes.persisted`
- `delivery.surface.emitted`
- `failure.runtime.reported`

`SEC-1` must emit approval events for classification and decisions:

- `approval.requested`
- `approval.classified`
- `approval.decided`
- `approval.granted`
- `approval.denied`

`OPS-2` must emit approval, side-effect, delivery, and failure audit events:

- `approval.requested`
- `approval.decided`
- `execution.side_effect.started`
- `execution.side_effect.completed`
- `delivery.audit.recorded`
- `failure.side_effect.reported`

## Rule

Telemetry helpers must stay observational. The contract can normalize event
shape and dispatch to a sink, but it must not encode backend-specific behavior
or business logic.
