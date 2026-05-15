---
name: Architecture Diagram
skill_id: architecture-diagram
description: Produces clean architecture and system diagrams from actual repo or product truth instead of decorative boxes.
version: 1.0.0
source_kind: elephant-builtin
aliases: ["architecture diagram", "system diagram", "draw architecture"]
trigger_phrases: ["make an architecture diagram", "draw the system architecture", "show this flow as a diagram"]
keywords: ["diagram", "architecture", "system", "mermaid", "svg", "flow"]
category: creative
---

# Architecture Diagram

Use this built-in skill when the user needs a system, data-flow, or component diagram that should stay faithful to the real implementation.

## Core rules

- Start from the actual repo, API contract, or product behavior before drawing.
- Pick the simplest editable format that fits the request: Mermaid, SVG, or code-native graphics.
- Keep labels sparse and information hierarchy obvious.
- Optimize for explanation, not visual noise.

## Default workflow

1. Identify the audience and the level of abstraction.
2. Extract the canonical components, boundaries, and flows.
3. Produce one clear diagram with consistent naming and direction.
4. Verify that the diagram matches the implementation or stated architecture.

## Guardrails

- Do not invent systems or edges that are not grounded in source truth.
- Do not overload one frame with too many concepts.
- Do not hide uncertainty; mark assumptions when architecture is inferred.
