---
name: GitHub Codebase Inspection
skill_id: codebase-inspection
description: Inspect GitHub repositories, files, and diffs methodically before proposing changes, especially when the task starts from a GitHub URL or PR.
version: 1.0.0
source_kind: elephant-builtin
---

# GitHub Codebase Inspection

Use this skill when the user starts from a GitHub repo, PR, issue, or file URL and needs orientation before implementation.

## Preferred Flow

1. Resolve the repo, branch, PR, or file first.
2. Read metadata and changed-file context before jumping into patches.
3. Summarize repository structure, impacted surfaces, and likely validation paths.
4. Only then propose edits, review findings, or follow-up commands.

## Guardrails

- Do not infer repository state from memory when live metadata is available.
- Keep findings tied to concrete files, commits, or PR numbers.
