---
name: Apple Reminders
skill_id: apple-reminders
description: Open Reminders.app and create macOS reminders with AppleScript when the user wants follow-ups in Apple's reminders system.
version: 1.0.0
source_kind: elephant-builtin
---

# Apple Reminders

Use this skill when the user wants a reminder tracked in Reminders.app instead of a transient todo list inside the current chat session.

## Preferred Flow

1. If the user only wants the app opened, use `open -a Reminders`.
2. For reminder creation, use `osascript` against the `Reminders` application.
3. Default to the default account and default list unless the user names a specific list.

## Reminder Creation Pattern

- Keep the reminder title short and literal.
- Put extra context in the reminder body/notes field when needed.
- Only attach a due date when the user explicitly gave one and it can be represented unambiguously.

## Guardrails

- Do not silently invent dates, times, or reminder lists.
- If the user asked for a durable reminder, prefer Reminders.app over the in-session todo tool.
- If AppleScript returns a permissions or automation error, surface it directly so the user can grant access.
