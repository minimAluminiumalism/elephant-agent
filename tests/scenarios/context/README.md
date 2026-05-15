# Context Scenarios

This directory seeds scenario fixtures for layered context assembly.

Track goals:

- overflow should trigger summarization rather than blind truncation
- interrupted sessions should recover continuity state explicitly through visible recovery behavior
- `EpisodeFrame` should keep `EpisodeFrozenContext` isolated from request-time volatility
- procedure overlays should stay optional and bounded
- request attachments should refresh per request without becoming durable state
- prompt rendering should stay structured and inspectable
- current-work-linked and corrected steady memory should survive compaction ahead of filler
- replay-focused requests should pull bounded reasoning and action history into a dedicated replay layer
