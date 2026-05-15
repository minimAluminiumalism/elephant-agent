---
name: GitHub Repo Management
skill_id: github-repo-management
description: Inspect repository metadata, branches, permissions, and operational state before changing settings or branch structure.
version: 1.0.0
source_kind: elephant-builtin
---

# GitHub Repo Management

Use this skill when the user wants repository-level administration rather than a single code change.

## Preferred Flow

1. Inspect repository metadata, default branch, and collaborator permissions first.
2. Confirm whether the task is read-only, branch management, labels, or PR automation.
3. Apply the smallest repository-level change that satisfies the ask.

## Guardrails

- Treat branch moves, force updates, and admin mutations as high risk.
- Report permission blockers instead of guessing.
