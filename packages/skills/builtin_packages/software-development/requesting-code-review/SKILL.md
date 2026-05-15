---
name: Requesting Code Review
skill_id: requesting-code-review
description: Package a code change for review with clear scope, risk notes, and validation evidence so reviewers can move quickly.
version: 1.0.0
source_kind: elephant-builtin
---

# Requesting Code Review

Use this skill when preparing a change for another engineer to review.

## Preferred Flow

1. Summarize the problem and the chosen fix.
2. Call out the touched surfaces and highest-risk behavior changes.
3. Include the exact validation you ran.
4. Name any open questions or known limitations.

## Guardrails

- Do not hand reviewers a mystery diff.
- Keep the review request scoped to the actual change.
