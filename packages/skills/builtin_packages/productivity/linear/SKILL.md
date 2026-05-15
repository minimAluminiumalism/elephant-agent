---
name: Linear
skill_id: linear
description: Work with Linear issues, projects, and triage flows while preserving status semantics and ownership clarity.
version: 1.0.0
source_kind: elephant-builtin
---

# Linear

Use this skill when the user wants issue tracking or planning work in Linear.

## Preferred Flow

1. Resolve the workspace, team, and issue before editing anything.
2. Read the current issue state and comments first.
3. When creating issues, keep titles crisp and put execution detail in the body.
4. When updating issues, preserve assignee, status, and project context unless the user asked to change them.

## Guardrails

- Do not silently close, re-prioritize, or reassign work.
- Distinguish between backlog capture and execution status.
