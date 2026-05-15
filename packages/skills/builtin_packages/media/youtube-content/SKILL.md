---
name: YouTube Content
skill_id: youtube-content
description: Fetch YouTube transcripts, summarize videos, and transform the transcript into chapters, notes, threads, or article-ready structure.
version: 1.0.0
source_kind: elephant-builtin
---

# YouTube Content

Use this skill when the user shares a YouTube URL or asks to summarize or repurpose video content.

## Preferred Flow

1. Extract the transcript first.
2. Verify language and transcript completeness before summarizing.
3. Chunk very long transcripts before transforming them.
4. Format the output to the user's requested form: summary, chapters, notes, thread, or article.

## Guardrails

- If transcripts are disabled or unavailable, say so explicitly.
- Distinguish quoted transcript content from your synthesis.
