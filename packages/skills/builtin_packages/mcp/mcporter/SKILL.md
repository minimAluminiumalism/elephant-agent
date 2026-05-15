---
name: mcporter
skill_id: mcporter
description: Discover, inspect, authenticate, and call MCP servers directly from the terminal through mcporter when a generic connector is not enough.
version: 1.0.0
source_kind: elephant-builtin
---

# mcporter

Use this skill when the user wants direct MCP server discovery or one-off MCP tool calls outside the already wired Elephant Agent connector surface.

## Preferred Flow

1. Probe the local setup with `npx mcporter list`.
2. Inspect one server's tools with schema output before calling anything.
3. Prefer `--output json` or equivalent structured output when tool results need to be parsed.
4. Use ad hoc HTTP or stdio server mode only when no configured server already exists.

## Guardrails

- Confirm auth or config changes before mutating mcporter config.
- If OAuth or browser auth is required, state that clearly instead of pretending it succeeded.
