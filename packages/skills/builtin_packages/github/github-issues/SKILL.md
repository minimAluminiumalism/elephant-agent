---
name: GitHub Issues
skill_id: github-issues
description: Triage GitHub issues, extract the real ask, and connect each issue to the relevant files, tests, or release surface before acting.
version: 1.0.0
source_kind: elephant-builtin
---

# GitHub Issues

Use this skill when the user wants issue summaries, triage, or issue-driven implementation work.

## Preferred Flow

1. Read the issue body, labels, and linked PRs or commits.
2. Separate the user-visible symptom from the likely implementation surface.
3. Identify whether the next step is clarification, reproduction, implementation, or release follow-up.

## Guardrails

- Do not collapse a vague issue into a concrete fix without checking the codebase.
- Call out missing reproduction steps or acceptance criteria.
