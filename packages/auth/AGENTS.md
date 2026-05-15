# Auth Package

This package owns credential and provider-auth behavior.

## Own Here

- provider auth profiles
- secret references
- rotation and cooldown metadata
- provider stickiness and pinning

## Do Not Own Here

- UI storage
- provider inference behavior

Keep secrets out of runtime-visible state by default.
