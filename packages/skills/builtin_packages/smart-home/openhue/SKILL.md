---
name: OpenHue
skill_id: openhue
description: Control Philips Hue lights, rooms, and scenes from the terminal through the OpenHue CLI with explicit targeting and safe defaults.
version: 1.0.0
source_kind: elephant-builtin
---

# OpenHue

Use this skill when the user wants Philips Hue lighting control from Elephant Agent.

## Preferred Flow

1. Inspect available lights, rooms, or scenes first.
2. Confirm the exact room or light name before applying changes.
3. Prefer scene activation when the user names a mood or preset.
4. Use direct brightness or temperature changes only when the user asks for them.

## Guardrails

- Treat whole-home or all-room changes as higher risk than a single light.
- If the bridge is not paired or reachable, report that directly.
