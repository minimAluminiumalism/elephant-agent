---
name: GitHub PR Workflow
skill_id: github-pr-workflow
description: Move cleanly through branch, diff, review, validation, and PR update steps without losing scope or repository-native workflow.
version: 1.0.0
source_kind: elephant-builtin
---

# GitHub PR Workflow

Use this skill when the task is explicitly about preparing, updating, or landing a pull request.

## Preferred Flow

1. Confirm the target branch and current diff scope.
2. Keep the change atomic.
3. Run the smallest repo-native validation path before publishing.
4. Summarize what changed, what was validated, and any remaining risk.

## Guardrails

- Do not widen the PR scope without saying so.
- Respect repository commit and release conventions.
