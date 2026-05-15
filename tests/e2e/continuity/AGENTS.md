# Continuity End-To-End Tests

Use this directory for app-level continuity flows that wrap the scenario
fixtures.

Rules:

- keep the e2e surface thin and scenario-driven
- each e2e file should map directly back to a scenario ID
- do not duplicate core scenario semantics here
- keep app-level assertions stable so kernel and module teams can consume them
