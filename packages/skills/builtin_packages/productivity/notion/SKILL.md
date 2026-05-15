---
name: Notion
skill_id: notion
description: Create, search, and update Notion pages or databases through the API or a narrow browser fallback when a Workspace lives in Notion.
version: 1.0.0
source_kind: elephant-builtin
---

# Notion

Use this skill when the user's workspace lives in Notion.

## Preferred Flow

1. Confirm the target page or database first.
2. Prefer API-based reads and writes when an integration key is already configured.
3. Keep page titles, property names, and database schema literal.
4. For large content updates, build the text first, then write once.

## Guardrails

- Do not invent page IDs, database IDs, or property names.
- Confirm destructive edits such as overwrites or archive actions.
