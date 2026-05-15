---
name: Shell Execution
skill_id: shell-execution
description: Keeps explicit shell work legible, bounded, and attached to the current workspace thread.
version: 1.0.0
source_kind: elephant-builtin
default_enabled: true
include_in_overlay: false
aliases: ["shell execution", "terminal command", "run shell"]
keywords: ["shell", "terminal", "command", "workspace"]
---

# Shell Execution

Use this built-in skill as the default posture for explicit shell work in the current workspace.

## Core rules

- Keep commands scoped to the active workspace unless the user clearly asks for something broader.
- Prefer inspect-before-write, explain risky commands, and surface concrete results instead of vague summaries.
- When a command should keep running, prefer background execution plus explicit follow-up inspection instead of blocking the whole turn.
