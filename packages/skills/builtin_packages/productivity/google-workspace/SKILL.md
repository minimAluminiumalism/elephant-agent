---
name: Google Workspace
skill_id: google-workspace
description: Handle Google Docs, Sheets, Drive, and related Workspace tasks through the narrowest available API or browser workflow.
version: 1.0.0
source_kind: elephant-builtin
---

# Google Workspace

Use this skill when the user wants work inside Google Docs, Sheets, Drive, or Calendar rather than only inside local files.

## Preferred Flow

1. Identify the exact Workspace app and document first.
2. Prefer structured APIs or connectors over brittle browser clicking.
3. If browser automation is required, keep the interaction narrow and verify the target document before editing.

## Guardrails

- Do not create or overwrite documents blindly.
- Confirm recipients before sharing or emailing Workspace artifacts.
