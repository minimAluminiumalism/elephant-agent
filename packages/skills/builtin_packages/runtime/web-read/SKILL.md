---
name: Web Read
skill_id: web-read
description: Keeps direct URL reading and text extraction available when a specific page matters more than search results.
version: 1.0.0
source_kind: elephant-builtin
default_enabled: true
include_in_overlay: false
aliases: ["web read", "read a url", "fetch page"]
keywords: ["web", "url", "page", "fetch", "read"]
---

# Web Read

Use this built-in skill when the user already knows the page that matters and the runtime should read that page directly.

## Core rules

- Prefer direct URL reading when the target page is known.
- Preserve concrete citations, titles, and source context instead of paraphrasing away the origin.
- Stop and report the real fetch problem if the page cannot be read reliably.
