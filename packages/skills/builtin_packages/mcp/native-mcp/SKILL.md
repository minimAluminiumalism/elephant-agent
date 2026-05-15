---
name: Native MCP
skill_id: native-mcp
description: Work through MCP-native resources and tools first when a connector already exposes the needed context or action surface.
version: 1.0.0
source_kind: elephant-builtin
---

# Native MCP

Use this skill when the needed data or action is already exposed through MCP resources or app tools.

## Preferred Flow

1. Prefer the connector-native resource or tool over shell scraping.
2. Read structured metadata before falling back to ad hoc commands.
3. Keep the task inside the connector boundary when that preserves correctness and auditability.

## Guardrails

- Do not duplicate a live MCP capability with brittle shell work unless the connector is missing a required action.
- State clearly when you are falling back outside MCP.
