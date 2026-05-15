# context.session-frame-request-refresh

## Purpose

Prove that `EpisodeFrame` rebuilds request-time context without turning the prompt
stack into a hidden durable store.

## Setup

- the stable runtime charter and guardrails already exist
- a session has active work, continuity memory, and at least one retrieved evidence ref
- at least one instructional skill can surface as a bounded procedure overlay
- runtime and request attachments can change between two consecutive requests

## Steps

1. keep `EpisodeFrozenContext` fixed across consecutive turns
2. rebuild `StateSnapshot` from current profile, work, and evidence slices
3. inject only the current request into `LoopContext`
4. refresh `RequestAttachments` from the live runtime/tool/activityspace state
5. render the final prompt in explicit `EpisodeFrame` layer order

## Expected Assertions

- `EpisodeFrozenContext` remains isolated from volatile recall and per-turn noise
- `StateSnapshot` explains which profile, work, and evidence slices were selected
- `LoopContext` changes with the current request instead of mutating durable truth
- no procedural overlay layer is injected
- `RequestAttachments` can refresh per request without becoming durable state
- the source trace stays inspectable and aligned with the rendered `EpisodeFrame`
