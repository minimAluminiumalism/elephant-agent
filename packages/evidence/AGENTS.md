# Evidence Package

This package owns recall, reflection, and semantic indexing.

## Own Here

- unified recall orchestration
- evidence lifecycle (capture, index, rerank, time-range)
- reflection runtime and window management
- personal model learning support
- semantic index factory and prefetch adapters

## Do Not Own Here

- storage implementation details (use packages/storage)
- provider-specific embedding logic (use packages/embeddings)
- direct kernel internals access
- deleted legacy memory-note or component-record surfaces
