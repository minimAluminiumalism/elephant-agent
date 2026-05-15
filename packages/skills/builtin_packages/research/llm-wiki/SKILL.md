---
name: LLM Wiki
skill_id: llm-wiki
description: Build concise, cross-linked wiki-style summaries for models, papers, techniques, or labs when the user wants durable knowledge capture.
version: 1.0.0
source_kind: elephant-builtin
---

# LLM Wiki

Use this skill when the user wants knowledge captured as a reusable wiki-style page rather than a one-off answer.

## Preferred Flow

1. Identify the entity or topic to document.
2. Gather canonical metadata first.
3. Organize the write-up into short sections: overview, key facts, links, and comparison context.
4. Preserve explicit source links when the user needs traceability.

## Guardrails

- Do not inflate uncertain claims into settled facts.
- Keep the page structured enough to update later.
