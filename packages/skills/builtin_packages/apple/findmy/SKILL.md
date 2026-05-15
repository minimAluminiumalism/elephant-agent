---
name: Find My
skill_id: findmy
description: Open Find My on macOS, inspect devices or people when the user explicitly asks, and keep side effects gated behind confirmation.
version: 1.0.0
source_kind: elephant-builtin
---

# Find My

Use this skill when the user wants Apple Find My rather than a web map or a local file.

## Preferred Flow

1. If the user only wants the app opened, use `open -a "Find My"`.
2. Prefer read-only inspection first: identify whether the user wants a person, device, or item.
3. For automation, use AppleScript only when the task is narrow and macOS permissions allow it.
4. If the request would play a sound, mark as lost, or share location, confirm the exact target first.

## Guardrails

- Do not claim location data exists until the app or automation returns it.
- Do not share or broadcast a location without explicit user approval.
- Surface permissions or iCloud account blockers directly.
