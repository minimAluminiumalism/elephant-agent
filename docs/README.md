# Docs

This repository keeps three active documentation layers on purpose:

- [`docs/agent/`](agent/README.md)
  - the repo and contributor harness
- [`docs/system-design/`](system-design/README.md)
  - the canonical product-facing system layer model
- [`docs/paper/`](paper/README.md)
  - the outward-facing system-report layer derived from the system layer model

Keep harness policy out of product-design docs, keep the system layer model as
the source of architecture truth, and treat `docs/paper/` as an external system
report rather than a second source of product design.
