---
name: Systematic Debugging
skill_id: systematic-debugging
description: Investigate bugs by reproducing, isolating, and validating a root-cause hypothesis before applying fixes.
version: 1.0.0
source_kind: elephant-builtin
---

# Systematic Debugging

Use this skill for test failures, regressions, flaky behavior, or confusing runtime errors.

## Preferred Flow

1. Read the full error and reproduce it consistently.
2. Isolate the failing component or assumption.
3. Compare broken behavior with a nearby working path.
4. Form one root-cause hypothesis.
5. Test the smallest change that proves or disproves it.

## Guardrails

- No random fix stacking.
- If you do not understand the failure yet, keep gathering evidence.
