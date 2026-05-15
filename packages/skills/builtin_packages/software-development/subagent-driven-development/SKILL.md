---
name: Subagent Driven Development
skill_id: subagent-driven-development
description: Split work into parallelizable, bounded tracks only when the tasks have disjoint ownership and the coordination cost is justified.
version: 1.0.0
source_kind: elephant-builtin
---

# Subagent Driven Development

Use this skill when a task genuinely benefits from parallel agents or worktrees.

## Preferred Flow

1. Keep the blocking path local.
2. Delegate only bounded sidecar work with clear ownership.
3. Avoid overlapping write scopes.
4. Integrate results quickly instead of waiting idly.

## Guardrails

- Do not delegate just to sound sophisticated.
- Do not spawn parallel work for tightly coupled edits.
