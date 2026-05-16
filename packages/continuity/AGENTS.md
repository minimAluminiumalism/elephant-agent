# Continuity Package

This package owns session continuity and resume projections.

## Own Here

- continuity runtime assembly
- resume projection records
- state continuity helpers for returning sessions

## Do Not Own Here

- app-specific resume rendering
- storage backend implementation
- Personal Model fact governance
- delivery adapter behavior

Continuity should express what can be resumed; apps decide how to present it.
