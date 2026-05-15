# Models/Auth Integration Tests

This directory holds cross-package tests for the `UX-1` adapter baseline.

## Own Here

- model adapter registry and routing tests
- secret-reference and credential-resolution tests
- preview-runtime integration between `packages/models` and `packages/auth`

## Rules

- keep tests deterministic and standard-library only
- do not require network access or external SDKs
- do not widen the write scope beyond `packages/models/**` and `packages/auth/**`
