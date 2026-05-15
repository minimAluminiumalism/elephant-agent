---
name: Claude Code
skill_id: claude-code
description: Guides operator-owned delegation to Claude Code when repo work benefits from a second coding lane or an interactive code agent.
version: 1.0.0
source_kind: elephant-builtin
aliases: ["claude code", "use claude code", "delegate to claude code"]
trigger_phrases: ["run this through claude code", "use claude code for this repo", "delegate this task to claude code"]
keywords: ["agent", "coding", "delegate", "repo", "worktree", "claude"]
category: autonomous-ai-agents
---

# Claude Code

Use this built-in skill when the user wants work routed through Claude Code or when a second coding lane would materially help.

## Core rules

- Keep the blocking path local unless delegation clearly reduces risk or latency.
- Run Claude Code against the real repo or an explicit worktree, not an ambiguous scratch directory.
- Pass bounded tasks with ownership, validation expectations, and merge criteria.
- Review Claude Code output against repo-native rules before treating it as done.

## Default workflow

1. Confirm whether Claude Code is the right lane versus local execution.
2. Identify the exact repo, worktree, files, and validation surface.
3. Hand off one bounded task with clear expected outputs.
4. Inspect the returned diff, run the relevant checks, and integrate intentionally.

## Guardrails

- Do not use Claude Code as a substitute for understanding the local codebase.
- Do not let multiple agent lanes edit the same files without explicit coordination.
- Do not claim Claude Code completed a task until the diff and validation are checked.
