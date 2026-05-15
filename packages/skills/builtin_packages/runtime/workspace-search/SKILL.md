---
name: Workspace Search
skill_id: workspace-search
description: Keeps local retrieval, file search, and nearby context gathering available in-session.
version: 1.0.0
source_kind: elephant-builtin
default_enabled: true
include_in_overlay: false
aliases: ["workspace search", "repo search", "code search"]
keywords: ["workspace", "repo", "search", "retrieve", "codebase"]
---

# Workspace Search

Use this built-in skill as the default search posture before making non-trivial repo changes.

## Core rules

- Search before editing when the code path is not already obvious.
- Prefer the smallest relevant set of files, symbols, and tests instead of browsing broadly without purpose.
- Keep retrieval grounded in the current repo rather than substituting generic assumptions.
