---
name: Excalidraw
skill_id: excalidraw
description: Shapes sketch-style diagrams and editable visual explanations for flows, product ideas, and architecture discussions.
version: 1.0.0
source_kind: elephant-builtin
aliases: ["excalidraw", "sketch diagram", "whiteboard diagram"]
trigger_phrases: ["make this in excalidraw", "sketch this system", "turn this into a whiteboard diagram"]
keywords: ["excalidraw", "diagram", "whiteboard", "sketch", "flow"]
category: creative
---

# Excalidraw

Use this built-in skill when the user wants an editable sketch-style diagram rather than a polished presentation graphic.

## Core rules

- Favor clarity, editable structure, and grouping over pixel-perfect ornament.
- Reduce each frame to the essential entities, flows, and callouts.
- Keep spatial grouping meaningful so the drawing still reads after edits.
- Preserve a human sketch feeling without making the content vague.

## Default workflow

1. Define the scene: entities, lanes, callouts, and arrows.
2. Group related items and keep one dominant reading direction.
3. Use concise labels and a restrained number of visual accents.
4. Check that the diagram remains understandable after export or handoff.

## Guardrails

- Do not pack dense prose into the drawing.
- Do not treat visual styling as a substitute for good structure.
- Do not output a sketch that loses the underlying logic of the flow.
