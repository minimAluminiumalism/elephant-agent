# Semantic Index Package

This package owns vector indexing and semantic search primitives.

## Own Here

- backend interfaces and sqlite-vec adapter
- index inventory and search result shapes
- embedding-to-search service orchestration

## Do Not Own Here

- context-window assembly policy
- evidence capture and ranking policy
- embedding provider implementation
- storage repository internals

Integrate through `packages/contracts`, `packages/embeddings`, and callers in
`packages/evidence` or `packages/context`.
