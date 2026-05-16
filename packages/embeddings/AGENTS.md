# Embeddings Package

This package owns the shared local embedding substrate for Elephant Agent.

## Own Here

- provider interfaces and registry
- canonical `elephant-embed` provider metadata
- dimension selection, normalization, and vector similarity helpers
- shared embedding service orchestration
- provider health and preload-state contracts

## Do Not Own Here

- runtime control policy
- semantic retrieval policy
- durable Step, Fact, Episode, or State truth
- app-specific bootstrap UX or operator wording
