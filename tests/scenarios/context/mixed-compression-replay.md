# context.mixed-compression-replay

## Purpose

Pull bounded reasoning and action replay into `EpisodeFrame` only when the current
request explicitly asks for earlier decision context.

## Setup

- the session already has structured-turn evidence with reasoning and action slots
- ordinary continuity recovery can proceed without replay detail
- the current request explicitly asks to replay an earlier decision path or action chain

## Steps

1. keep `EpisodeFrozenContext` unchanged
2. rebuild `StateSnapshot` from durable profile, work, and steady continuity slices
3. allocate a dedicated replay budget only because the request asks for earlier decision context
4. pull the relevant reasoning slice at a bounded compression level
5. pull the relevant action slice at a different compression level when needed
6. render the final prompt with an inspectable source trace

## Expected Assertions

- ordinary prompts do not include replay detail by default
- replay-focused requests create a dedicated `EpisodeReplay` instead of mutating `EpisodeFrozenContext`
- one replay slice may use compressed reasoning while another keeps raw action detail
- the source trace explains which structured-turn evidence entered the replay layer and which replay budget choices were made
