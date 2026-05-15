# API App

This surface exposes Elephant Agent programmatically.

## Own Here

- HTTP or RPC routing
- request and response translation
- auth at the API boundary
- app-level health and operator endpoints

## Do Not Own Here

- core cognition
- provider-specific prompt behavior
- hidden data model forks

Keep the API contract thin and map it onto package-level interfaces.
