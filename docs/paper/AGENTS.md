# Paper Drafting Rules

This directory is for outward-facing paper artifacts only.

## Keep Here

- system-report LaTeX sources
- paper-specific section drafts and compile assets
- narrative that turns `../system-design/` into an external system report

## Do Not Keep Here

- harness policy
- repo execution plans
- implementation-only notes that still belong in `../system-design/`
- fabricated citations or unverifiable BibTeX entries
- historical system-design vocabulary that conflicts with the current layer model

## Read First

1. [README.md](README.md)
2. [../system-design/README.md](../system-design/README.md)
3. [../system-design/system-layer-model.md](../system-design/system-layer-model.md)

## Working Rules

- use `docs/system-design/system-layer-model.md` as the source of truth
- write the paper as an external system report, not as an implementation plan
- present the accepted design as a realized system when the user asks for a
  technical-report style draft
- keep claims aligned to the current layer model: `Step`, `Loop`, `Episode`,
  `Elephant State`, `Personal Model`, semantic recall, and background reflect jobs
- never add citations from memory; only add verified references to
  `references.bib`
