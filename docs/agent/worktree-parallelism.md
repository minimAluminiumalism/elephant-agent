# Worktree Parallelism

## Goal

Make concurrent contributor or multi-agent work safe by default.

## Rules

- one worktree owns one branch
- one branch owns one clear task or subtask
- avoid overlapping write scopes across active worktrees
- keep local runtime state out of tracked files
- if two worktrees need the same hotspot, sequence them through a plan instead of concurrent edits

## Canonical Commands

```bash
make agent-worktree-add WORKTREE_NAME=harness-docs WORKTREE_BRANCH=docs/harness-docs
make agent-worktree-list
make agent-worktree-remove WORKTREE_NAME=harness-docs
```

## Practical Guardrails

- use `docs/agent/plans/` to assign ownership when several agents are active
- keep the user talking to one main session; treat worker sessions as subordinate execution lanes
- launch the largest safe ready subset of tracks in parallel when write scopes are disjoint
- pin worker sessions to `gpt-5.4` explicitly instead of inheriting an implicit model choice
- once the main session has launched clear assignment packets for the ready lanes, it may return and resume review or integration later
- keep docs, harness-exec, and product-code changes separable so review and cherry-pick stay tractable
- ship one branch increment at a time with one atomic commit when the diff is controlled
- create the first commit on `main` before relying on worktrees
