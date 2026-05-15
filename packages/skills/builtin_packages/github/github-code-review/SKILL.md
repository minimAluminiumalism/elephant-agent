---
name: GitHub Code Review
skill_id: github-code-review
description: Review pull requests with a bug-first mindset, grounding findings in concrete diff context and repository behavior.
version: 1.0.0
source_kind: elephant-builtin
---

# GitHub Code Review

Use this skill when the user asks for a PR review or wants actionable findings from a GitHub diff.

## Review Order

1. Read PR metadata and changed files.
2. Focus first on correctness, regressions, missing tests, and broken assumptions.
3. Keep findings concise, severity-ordered, and file-grounded.
4. Only after findings should you summarize the broader change.

## Guardrails

- Avoid style-only noise unless it hides a real defect.
- If there are no findings, say so explicitly and mention residual risk.
