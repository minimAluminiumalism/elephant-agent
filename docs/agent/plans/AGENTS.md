# Plans Directory Rules

Use this directory for durable execution plans that span multiple sessions,
contributors, or worktrees.

## What Belongs Here

- roadmap documents
- multi-agent task decomposition
- phased migrations
- release-readiness tracks

## What Does Not Belong Here

- product architecture prose that should live under `docs/system-design/`
- ADR content that belongs under `docs/agent/adr/`
- unresolved scratch notes that should stay in chat or local-only notes

## Authoring Rules

- every plan should state goal, scope, non-goals, tracks, dependencies,
  validation, and exit criteria
- parallel plans should assign explicit write scopes so active worktrees do not
  overlap by accident
- if one plan becomes the active roadmap, update it instead of forking a second
  competing roadmap file
- when a track needs a contract or architectural decision, land that in
  `docs/agent/adr/` or `docs/system-design/` and link it from the plan
