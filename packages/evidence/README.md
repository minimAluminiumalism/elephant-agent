# Evidence

This package owns request-time evidence retrieval and wake-recovery helpers.

It keeps retrieval explainable and rebuildable:

- explicit `EvidenceRetrievalRequest` inputs
- lexical plus shared `packages/embeddings` matryoshka-style vector scoring
- scope-aware reranking tied to active work and continuity hints
- `ResumePacket` construction for wake and resume flows
- deterministic embedding index rebuild and invalidation policy derived from canonical evidence rows
