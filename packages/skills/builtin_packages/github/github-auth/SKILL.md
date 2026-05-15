---
name: GitHub Auth
skill_id: github-auth
description: Verify GitHub CLI or connector authentication, identify the active identity, and debug missing permissions before other GitHub operations.
version: 1.0.0
source_kind: elephant-builtin
---

# GitHub Auth

Use this skill when GitHub operations fail because identity, token, or repository access is unclear.

## Preferred Flow

1. Check the active identity first with the available GitHub connector or `gh auth status`.
2. Confirm whether the issue is missing auth, wrong account, or missing repo permission.
3. Re-run the smallest failing GitHub action after auth is fixed.

## Guardrails

- Never print secrets or copy tokens back into chat.
- Report whether the blocker is account, scope, installation, or repo permission.
