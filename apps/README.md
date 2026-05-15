# Apps

Runnable product and operator surfaces live here.

Current planned surfaces:

- `cli/`
  - primary user-facing runtime surface
- `api/`
  - programmatic and remote orchestration surface
- `gateway/`
  - messaging ingress and delivery process
- `site/`
  - public website, docs, and release-facing web surface

Working rules:

- app code should compose packages; it should not become the source of truth for core cognition
- keep transport, rendering, and process lifecycle here
- move reusable logic down into `packages/` before it becomes shared across apps
- add or update a local `AGENTS.md` when an app surface gains non-obvious invariants
