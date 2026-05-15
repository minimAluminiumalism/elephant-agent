# Task Cards Rules

Use this directory for directly assignable implementation units.

## What Belongs Here

- one card per roadmap track or subtrack
- clear write-scope ownership for one branch and one worktree
- explicit dependencies, validation, and handoff rules

## What Does Not Belong Here

- stable architecture decisions that belong in `../adr/`
- broad sequencing graphs that belong in `../plans/`
- large implementation journals that should stay in branch history or PR text

## Authoring Rules

- every card must link the roadmap track and its governing ADR
- every card must state readiness, dependencies, write scope, deliverables,
  validation, and handoff
- one card should be completable as one controlled branch increment
- if a card is too large for one atomic branch increment, split it before
  assigning it
