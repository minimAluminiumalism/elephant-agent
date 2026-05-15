# companion.text-first-continuity

## Purpose

Keep companion continuity stable while staying text-first.

## Setup

- a profile defines a canonical identity charter, personality, and companion settings
- a session has already been started and resumed
- the user expects continuity without voice transport

## Steps

1. load the profile and canonical identity state
2. resume the session lineage
3. inspect the active persona state from the CLI
4. continue in text-first mode without changing identity

## Expected Assertions

- personality settings survive resumption
- canonical identity remains visible
- text-first mode remains explicit
- relationship continuity stays inspectable
