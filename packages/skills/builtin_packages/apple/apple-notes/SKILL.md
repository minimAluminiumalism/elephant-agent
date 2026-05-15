---
name: Apple Notes
skill_id: apple-notes
description: Open Notes.app and create or update iCloud notes on macOS using memo when possible and AppleScript when direct app automation is more reliable.
version: 1.0.0
source_kind: elephant-builtin
aliases: ["apple notes", "notes app", "notes.app", "苹果备忘录", "备忘录"]
trigger_phrases: ["open notes", "open apple notes", "打开苹果备忘录", "打开备忘录", "写到备忘录", "记到备忘录"]
keywords: ["notes", "note", "notes.app", "apple notes", "备忘录", "苹果"]
---

# Apple Notes

Use this skill when the user wants work to land in Apple Notes rather than in agent memory or a markdown file.

## Preferred Flow

1. If the user only wants Notes.app opened, use `open -a Notes`.
2. If the task needs a note created or updated, probe the `memo` CLI first with `memo notes --help`.
3. If `memo` is missing and Notes automation is clearly the shortest path, install it with:
   `brew tap antoniorodr/memo && brew install antoniorodr/memo/memo`
4. Use `memo notes -a "Title"` when a non-interactive add path is available.
5. If `memo` falls into an editor or another interactive flow, fall back to `osascript` and create the note directly inside Notes.app.

## AppleScript Fallback

- Default to the iCloud account and the `Notes` folder unless the user names a different folder.
- Keep the note title and body in shell variables, then pass them into a quoted heredoc so multiline text survives intact.
- After creating the note, activate Notes.app so the user can immediately see the result.

## Guardrails

- Prefer Apple Notes only when the user wants Apple-device sync or explicitly asks for Notes.app.
- Use the memory tool for agent-internal facts that should not become user-facing notes.
- Preserve markdown/plain text exactly as supplied; do not rewrite punctuation or list formatting while shell-escaping.
- If note creation fails through both `memo` and AppleScript, report the concrete error and stop instead of pretending the note exists.
