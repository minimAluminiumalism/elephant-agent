# ADR Directory Rules

Use this directory for stable structural decisions that should outlive one
execution branch.

## What Belongs Here

- boundary decisions
- lifecycle decisions
- storage and state-model decisions
- extension-contract decisions
- surface and deploy decisions that will shape multiple implementations

## What Does Not Belong Here

- temporary execution sequencing
- per-branch scratch notes
- unresolved brainstorming without a concrete decision

## Authoring Rules

- keep one decision per ADR
- use `adr-####-slug.md` naming
- include `Status`, `Context`, `Decision`, and `Consequences`
- link the relevant roadmap track or task card when the ADR exists to unblock work
- mark ADRs as `Proposed` until the integration captain treats them as accepted
