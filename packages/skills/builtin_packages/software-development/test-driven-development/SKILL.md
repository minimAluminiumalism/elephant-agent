---
name: Test Driven Development
skill_id: test-driven-development
description: Drive behavior changes through a failing test, the smallest working implementation, and then cleanup once the behavior is locked.
version: 1.0.0
source_kind: elephant-builtin
---

# Test Driven Development

Use this skill when the behavior can be expressed clearly in tests before the implementation is obvious.

## Preferred Flow

1. Write or identify the failing test first.
2. Make the minimal change that turns it green.
3. Refactor only after behavior is protected.
4. Keep the test focused on one behavior.

## Guardrails

- Do not add broad, fragile snapshot coverage when a precise assertion is possible.
- If the repo has a stronger existing testing pattern, follow it.
