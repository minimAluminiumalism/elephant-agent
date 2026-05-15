# Continuity Scenario Fixtures

Use this directory for longitudinal product-thesis fixtures.

Rules:

- keep scenario IDs stable once published
- prefer one file per scenario so module teams can extend them independently
- define expected assertions explicitly, not as prose-only intent
- do not bake in temporary runtime details that will collapse once kernel and
  module implementations land
- treat these fixtures as the product truth for continuity until runtime tests
  exist
