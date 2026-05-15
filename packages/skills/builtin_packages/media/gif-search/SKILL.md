---
name: GIF Search
skill_id: gif-search
description: Search and download reaction GIFs through the Tenor API using curl and jq when the user wants lightweight media retrieval.
version: 1.0.0
source_kind: elephant-builtin
aliases: ["gif search", "reaction gif", "tenor gif", "动图", "表情包"]
trigger_phrases: ["find a gif", "search a gif", "find a reaction gif", "找个 gif", "找个动图", "找个 reaction gif"]
keywords: ["gif", "reaction", "tenor", "动图", "表情包"]
---

# GIF Search

Use this skill when the user wants a GIF rather than a still image or a generated asset.

## Preferred Flow

1. Check that `TENOR_API_KEY` is available.
2. Search Tenor with a narrow query.
3. Prefer lightweight preview formats when only a link is needed.
4. Download the full GIF only when the user needs a local file.

## Guardrails

- Do not claim media is available if the API key is missing or the query returned no results.
- Keep file size in mind when choosing between full GIF and preview variants.
