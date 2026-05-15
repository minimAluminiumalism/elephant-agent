---
name: Skill Creator
skill_id: skill-creator
description: Guide for creating effective Elephant Agent skills. Use this skill when users want to create a new skill or update an existing skill that extends Elephant Agent with specialized knowledge, workflows, or tool integrations.
version: 1.0.0
source_kind: elephant-builtin
aliases: ["creating skills", "create a skill", "write a skill", "make a skill", "skill authoring", "skill writing", "写 skill", "创建 skill"]
trigger_phrases: ["create a skill", "write a skill", "make this a skill", "save this as a skill", "写一个 skill", "做成 skill", "写一个 builtin skill", "写一个 built-in skill"]
keywords: ["skill", "skill package", "SKILL.md", "builtin skill", "built-in skill", "agent skill"]
---

# Skill Creator

This skill provides guidance for creating effective Elephant Agent skills.

## About Skills

Skills are modular, self-contained folders that extend Elephant Agent with specialized knowledge, workflows, and reusable operating procedures. They are the right surface when the capability can be expressed as instructions plus existing tools or shell commands.

Use a tool instead when the behavior needs deterministic runtime logic, deep auth wiring, binary handling, streaming, or an integration that must execute precisely every time.

## Core Principles

### Keep It Concise

The context window is shared. Assume Elephant Agent is already generally capable and only add the domain-specific guidance it actually needs.

Prefer:
- short trigger descriptions
- compact procedures
- references or scripts for bulky detail

Avoid long essay-style explanations that restate obvious things.

### Set the Right Degree of Freedom

- Use high-level instructions when multiple approaches are acceptable.
- Use tighter step sequences when the workflow is fragile or error-prone.
- Use scripts or helper assets when the same deterministic logic would otherwise be rewritten repeatedly.

### Protect Validation Integrity

Validate a new or revised skill on realistic prompts. If the skill is supposed to auto-route, test at least one explicit phrase and one contextual trigger instead of assuming the metadata is good enough.

## Anatomy of an Elephant Agent Skill

Every skill package must have a `SKILL.md`. Optional bundled resources can live beside it when they materially improve execution:

- `scripts/` for deterministic helpers
- `references/` for detailed documentation that should only be loaded when needed
- `assets/` for templates or output resources

The frontmatter should stay explicit:

- `name`
- `skill_id`
- `description`
- `version`
- `source_kind`

Add `aliases`, `trigger_phrases`, and `keywords` when the skill should be discoverable through natural-language routing or slash commands.

## Preferred Flow

1. Understand the concrete use cases first.
   Identify what kinds of requests should trigger the skill and what successful use looks like.

2. Decide the right destination shelf.
   Use `packages/skills/builtin_packages/` only for repo-shipped, generally useful skills that should travel with Elephant Agent.
   Use the shared Elephant Agent skill shelf or the runtime skill authoring flow for user-owned or experience-derived skills.

3. Design for progressive disclosure.
   Keep the `SKILL.md` body focused on core workflow guidance.
   Move bulky reference material into `references/` when it would otherwise bloat the skill body.

4. Write the skill package.
   Create one directory named after the skill id.
   Add a `SKILL.md` with precise trigger metadata and a compact operational body.

5. Reuse existing patterns instead of inventing a new style.
   Follow nearby built-in skills when the domain is similar.

6. Validate the package after writing it.
   Load it through `/skills view` or the runtime inspector.
   Confirm the `skill_id`, summary, and slash metadata resolve as expected.

## Guardrails

- Do not turn a one-off workaround into a repo-bundled builtin skill.
- Do not duplicate an existing skill with only cosmetic wording changes; tighten or extend the existing skill instead.
- Do not bury the trigger conditions in the body; the metadata must be clear enough for discovery.
- When a skill depends on a platform, CLI, API key, or external prerequisite, say that directly.
- When promoting a skill into the builtin shelf, keep trigger metadata conservative so unrelated prompts do not preload it accidentally.
