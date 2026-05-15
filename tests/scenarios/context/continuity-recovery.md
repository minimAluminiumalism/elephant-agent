# context.continuity-recovery

## Purpose

Recover active current work and continuity state after a gap or interruption.

## Setup

- the session has an interruption state
- the active current-work item exists in durable elephant
- prior steady history can be summarized safely

## Steps

1. reload Episode and State current work
2. summarize steady history into a continuity note
3. schedule retrieval for current-work-linked memories
4. render a prompt that explains the next move

## Expected Assertions

- the interruption state influences the plan
- the active current-work item remains visible in the bundle
- the rendered prompt explains the next move instead of hiding it
- the source trace shows which State current-work and memory ids entered the bundle
- continuity recovery does not require a separate prompt stack
