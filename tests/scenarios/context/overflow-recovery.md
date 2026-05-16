# context.overflow-recovery

## Purpose

Prove that context overflow produces summaries and explicit retrieval scheduling
instead of blind truncation.

## Setup

- the session has more history than the current budget can fit
- at least one active current-work item is still relevant
- some recall evidence items are current-work-linked and some are filler

## Steps

1. allocate an explicit token budget across layers
2. summarize the steady layer when it no longer fits
3. schedule retrieval for the most relevant memories
4. render the final prompt bundle

## Expected Assertions

- token allocation is explicit for each layer
- overflow is recorded and visible
- the prompt remains structured and readable
- current-work-linked evidence are prioritized over filler evidence
- the source trace explains which memories were compacted away and which entered the bundle
