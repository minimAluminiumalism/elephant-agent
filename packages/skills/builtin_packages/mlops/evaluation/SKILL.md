---
name: Evaluation
skill_id: evaluation
description: Frames model, prompt, and system evaluation as a reproducible experiment with baselines, datasets, and explicit metrics.
version: 1.0.0
source_kind: elephant-builtin
aliases: ["eval", "evaluation", "benchmark models"]
trigger_phrases: ["evaluate this model", "benchmark these prompts", "set up an eval harness"]
keywords: ["evaluation", "benchmark", "dataset", "metric", "baseline", "reproducibility"]
category: mlops
---

# Evaluation

Use this built-in skill when the user wants to compare prompts, models, retrieval setups, or agent behaviors with something stronger than anecdotes.

## Core rules

- Define the task, dataset, metric, and baseline before running comparisons.
- Keep eval inputs and scoring rules stable enough to reproduce.
- Separate offline benchmarking from product acceptance criteria.
- Report both quantitative outcomes and obvious failure modes.

## Default workflow

1. Identify the decision the evaluation should support.
2. Build or select the smallest credible dataset and metric set.
3. Run the baseline and candidate systems under the same conditions.
4. Summarize the tradeoffs, regressions, and confidence level.

## Guardrails

- Do not declare wins from cherry-picked examples.
- Do not mix incomparable prompts, models, or retrieval settings in one score line.
- Do not skip failure-case inspection when the average looks good.
