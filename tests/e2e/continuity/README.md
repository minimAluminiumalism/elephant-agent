# Continuity E2E Wrappers

This directory maps the scenario fixtures into app-level runtime flows.

Purpose:

- prove the CLI and API surfaces can consume the continuity vocabulary
- keep app-facing assertions aligned with the scenario truth
- provide stable hooks for kernel, planning, memory, and `companion profile`
  implementation work

Suggested wrapper shape:

- `cli.resume`
- `cli.interrupted-work`
- `api.session-recovery`
- `api.next-step-explanation`
- `gateway.text-continuity`

Each wrapper should point back to one or more scenario IDs from
`tests/scenarios/continuity/scenarios.yaml`.
