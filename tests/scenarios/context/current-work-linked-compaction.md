# context.current-work-linked-compaction

## Purpose

Prefer current-work-linked and corrected steady evidence during compaction instead
of a blind recency slice.

## Setup

- the session is resuming after a gap
- steady history contains both current-work-linked memory and newer filler memory
- one of the current-work-linked evidence is corrected and should remain visible

## Steps

1. score steady memories for continuity recovery
2. compact the steady layer under a constrained token budget
3. retain current-work-linked and corrected Personal Model fact ahead of filler
4. render the prompt and source trace

## Expected Assertions

- current-work-linked steady evidence is retained ahead of fresher filler evidence
- corrected Personal Model fact remains visible in the steady layer during recovery
- the source trace explains which filler evidence were compacted away
- the rendered prompt stays structured and inspectable

## Downstream Extensions

- `packages/context/**` should own deterministic long-context selection and traceability
- `packages/evidence/**` and `packages/semantic_index/**` should keep corrected durable fact visible to context assembly
- `PAI-2` and `PAI-3` should be able to rely on this continuity behavior
