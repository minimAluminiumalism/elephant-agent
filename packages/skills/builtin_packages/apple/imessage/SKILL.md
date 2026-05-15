---
name: iMessage
skill_id: imessage
description: Read or send Messages.app conversations on macOS through CLI or AppleScript with explicit confirmation before outbound sends.
version: 1.0.0
source_kind: elephant-builtin
---

# iMessage

Use this skill when the user wants Apple Messages, SMS, or iMessage rather than email or another chat tool.

## Preferred Flow

1. If the user only wants Messages opened, use `open -a Messages`.
2. Prefer the `imsg` CLI when available: `brew install steipete/tap/imsg`.
3. Use read-only commands first for chat lookup or history.
4. Before sending, confirm the recipient, message text, and any attachment path.
5. If CLI automation is unavailable, fall back to AppleScript only for narrow, explicit actions.

## Guardrails

- Never send to an ambiguous contact.
- Never send bulk or repeated outbound messages without clear approval.
- Report Full Disk Access or Automation permission errors directly.
