---
name: Vector Databases
skill_id: vector-databases
description: Guides retrieval-store design, indexing, and query behavior for embedding-backed systems without confusing storage with application truth.
version: 1.0.0
source_kind: elephant-builtin
aliases: ["vector db", "vector database", "embedding store"]
trigger_phrases: ["set up a vector database", "design the retrieval store", "index embeddings for search"]
keywords: ["vector database", "retrieval", "embeddings", "index", "chunking", "filtering"]
category: mlops
---

# Vector Databases

Use this built-in skill when the user needs an embedding-backed retrieval store, semantic search index, or hybrid filtering design.

## Core rules

- Define the retrieval task before selecting an index or vendor.
- Make chunking, metadata, freshness, and filter behavior explicit.
- Keep canonical application truth outside the vector index unless the system is designed that way.
- Evaluate retrieval quality, not just index build success.

## Default workflow

1. Identify the query patterns, corpus shape, and update frequency.
2. Choose the embedding and indexing strategy that matches that workload.
3. Design metadata filters, ids, and refresh behavior intentionally.
4. Test retrieval quality with representative queries before scaling up.

## Guardrails

- Do not equate a working index build with a good retrieval system.
- Do not hide stale-data or reindex costs.
- Do not use the vector store as a vague substitute for product data modeling.
