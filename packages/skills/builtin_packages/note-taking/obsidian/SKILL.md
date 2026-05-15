---
name: Obsidian
skill_id: obsidian
description: Work with vault-backed markdown notes in Obsidian, preserving links, filenames, and existing note structure.
version: 1.0.0
source_kind: elephant-builtin
---

# Obsidian

Use this skill when the user wants work to land in an Obsidian vault rather than in Apple Notes or a generic markdown file.

## Preferred Flow

1. Identify the target vault and note path first.
2. Preserve wikilinks, frontmatter, tags, and existing headings.
3. Use plain markdown edits unless the user explicitly wants Obsidian-specific automation.

## Guardrails

- Do not move or rename notes unless the user asked for it.
- Avoid flattening wikilinks into plain text.
