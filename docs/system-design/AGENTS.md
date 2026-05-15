# System Design Docs

This directory is for product-facing architecture and technical design only.

## Keep Here

- canonical system layer model
- future product/runtime boundaries derived from that model
- implementation-oriented design convergence after the model is accepted

## Do Not Keep Here

- contributor workflow policy
- CI or harness rules
- temporary execution notes that belong in `docs/agent/plans/`
- historical design drafts that conflict with the current layer model

## Read First

1. [README.md](README.md)
2. [system-layer-model.md](system-layer-model.md)

## Working Rules

- treat the system layer model as the only active design source of truth in this
  directory
- when a technical design decision becomes stable enough to affect repo
  structure, update the matching local `AGENTS.md` files and repo maps
- keep product-design docs implementation-oriented, but do not let them become
  hidden source code contracts
