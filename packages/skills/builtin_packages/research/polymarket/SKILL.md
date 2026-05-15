---
name: Polymarket
skill_id: polymarket
description: Inspect prediction-market questions, prices, and resolution conditions carefully before summarizing or comparing market signals.
version: 1.0.0
source_kind: elephant-builtin
---

# Polymarket

Use this skill when the user wants prediction-market context or market-based probability signals.

## Preferred Flow

1. Identify the exact market question and resolution condition.
2. Read the current price or implied probability.
3. Separate the market signal from your own interpretation.
4. Note the timestamp when reporting fast-moving market data.

## Guardrails

- Do not treat market prices as facts.
- Be explicit that these values are time-sensitive.
