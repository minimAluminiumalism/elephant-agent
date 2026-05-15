---
name: OpenCode
skill_id: opencode
description: Frames OpenCode as an operator-controlled coding lane for bounded implementation or review work inside a real repository.
version: 1.0.0
source_kind: elephant-builtin
aliases: ["opencode", "use opencode", "delegate to opencode"]
trigger_phrases: ["run this with opencode", "use opencode for this task", "delegate this repo work to opencode"]
keywords: ["opencode", "agent", "coding", "delegate", "repo"]
category: autonomous-ai-agents
---

# OpenCode

Use this built-in skill when OpenCode is the requested execution lane or when an extra repo-aware coding agent would help with a bounded task.

## Core rules

- Keep the operator in control of scope, workspace, and validation.
- Provide concrete task packets instead of broad aspirational prompts.
- Reconcile OpenCode output with the current branch and user-owned edits before merge.
- Use the same repo-native quality bar you would apply to a local implementation.

## Default workflow

1. Confirm the repo, target files, and expected deliverable.
2. Isolate the work if it should not land directly in the current checkout.
3. Delegate one bounded implementation or review task.
4. Inspect, validate, and integrate the returned work.

## Guardrails

- Do not present OpenCode as an autonomous source of truth.
- Do not overlap its write scope with other live agents unless the coordination plan is explicit.
- Do not ship its output without repo-native checks.
