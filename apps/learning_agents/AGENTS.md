# Learning Agents App

This app is a compatibility shim for background learning workers.

## Own Here

- app-level import compatibility for learning worker entrypoints
- process wiring that delegates to the current reflection/learning runtime

## Do Not Own Here

- new learning algorithms
- Personal Model governance
- storage schema or repository behavior
- user-facing dashboard or CLI rendering

Prefer adding new background-learning behavior under package or reflect-app
surfaces, then keep this shim minimal.
