# Packages Boundary

This directory contains reusable runtime modules and extension contracts.

## Working Rules

- package code should be reusable by multiple apps
- keep dependencies directional and explicit
- prefer integrating through `packages/contracts/` and `packages/capabilities/`
- do not let one package reach into another package's private internals when a contract can express the dependency
