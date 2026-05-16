# Operator Package

This package owns service and daemon management primitives.

## Own Here

- operator runtime helpers
- procedure projections for local service management
- daemon/service state abstractions

## Do Not Own Here

- user-facing CLI command formatting
- deploy-specific unit files
- kernel turn execution
- provider credential storage

Keep operator code reusable by CLI, API, and deployment surfaces.
