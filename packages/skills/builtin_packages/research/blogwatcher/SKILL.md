---
name: Blogwatcher
skill_id: blogwatcher
description: Monitor blog or website updates, compare publish dates, and summarize deltas rather than repeating unchanged content.
version: 1.0.0
source_kind: elephant-builtin
---

# Blogwatcher

Use this skill when the user wants recent updates from blogs, labs, or documentation sites.

## Preferred Flow

1. Identify the canonical site or feed.
2. Compare publish dates and freshness before summarizing.
3. Highlight what changed since the last known checkpoint.

## Guardrails

- Do not call something new without checking dates.
- Separate announcement text from your synthesis.
