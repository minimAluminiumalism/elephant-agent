# Reflect App

This app owns composable background reflection runners.

## Own Here

- reflection runner orchestration
- feature-specific reflection prompts
- evidence packets for diary, dream, recall, skills, and Personal Model review
- app-level wiring for background reflection jobs

## Do Not Own Here

- durable Personal Model schema
- storage repository internals
- CLI or dashboard rendering
- kernel turn execution

Keep feature modules thin over `packages/evidence`, `packages/tools`, and
`packages/storage`.
