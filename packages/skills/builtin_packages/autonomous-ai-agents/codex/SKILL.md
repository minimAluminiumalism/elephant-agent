---
name: Codex
skill_id: codex
description: Guides operator-owned delegation to Codex when the task fits a bounded coding lane, review pass, or worktree-isolated implementation track.
version: 1.0.0
source_kind: elephant-builtin
aliases: ["codex", "use codex", "delegate to codex"]
trigger_phrases: ["run this in codex", "delegate this to codex", "use codex on this repo"]
keywords: ["codex", "coding", "delegate", "review", "worktree", "agent"]
category: autonomous-ai-agents
---

# Codex

Use this built-in skill when the user wants a task executed through Codex or when a dedicated coding lane is the cleanest way to isolate work.

## Core rules

- Prefer repo-native instructions and validation over generic agent folklore.
- Delegate only work with a clear boundary, write scope, and success condition.
- Use worktrees or isolated branches when the task is not safe inside the current checkout.
- Treat Codex output as a candidate change set that still needs human review and repo validation.

## Default workflow

1. Decide whether the next blocking step should stay local or move to Codex.
2. Define the task packet: scope, files, tests, branch or worktree, and ship expectations.
3. Review the returned changes against the harness and any user-owned edits.
4. Validate, integrate, and summarize the outcome in operator language.

## Guardrails

- Do not delegate vague exploratory work just to create agent theater.
- Do not send Codex into a dirty shared checkout without a coordination plan.
- Do not skip validation because the delegated run looked confident.
