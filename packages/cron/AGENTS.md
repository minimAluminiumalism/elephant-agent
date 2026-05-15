# Cron Package

This package owns durable scheduled job state and schedule evaluation.

## Own Here

- cron job schemas and persistence
- schedule parsing and next-run computation
- due-job selection and state transitions

## Do Not Own Here

- CLI rendering
- app-specific delivery surfaces
- provider-specific execution behavior
