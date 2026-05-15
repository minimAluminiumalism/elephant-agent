---
name: Himalaya Email
skill_id: himalaya
description: Work with IMAP email from the terminal using Himalaya for inbox reads, draft review, and carefully confirmed outbound sends.
version: 1.0.0
source_kind: elephant-builtin
---

# Himalaya Email

Use this skill when the user wants terminal-native email handling and an account is already configured for `himalaya`.

## Preferred Flow

1. Probe the setup with `himalaya --help` and `himalaya accounts`.
2. Prefer read-only mailbox inspection before composing replies.
3. For message searches, keep filters narrow and summarize before taking action.
4. Draft outbound mail in plain text first, then confirm recipients and subject before sending.

## Guardrails

- Treat outbound mail as a high-side-effect action.
- Do not invent recipients, attachments, or account names.
- If account configuration is missing, stop and report the missing setup.
