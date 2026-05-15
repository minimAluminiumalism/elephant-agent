# Apps Boundary

This directory contains runnable product and operator surfaces.

## Keep Here

- CLI entrypoints
- API servers
- gateway processes
- website and operator-facing web apps

## Do Not Keep Here

- durable record schemas
- core planning, memory, or context policy
- provider-specific logic that belongs in `packages/models/` or `packages/auth/`

## Working Rules

- apps should depend on packages, not on each other
- keep each app thin enough that it can be replaced or split without rewriting the kernel
- when an app needs shared behavior, move that behavior into `packages/`
