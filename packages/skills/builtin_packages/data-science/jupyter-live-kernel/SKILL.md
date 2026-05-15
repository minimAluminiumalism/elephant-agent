---
name: Jupyter Live Kernel
skill_id: jupyter-live-kernel
description: Guides notebook-first analysis with reproducible kernels, inspectable data loading, and explicit promotion paths back into durable code.
version: 1.0.0
source_kind: elephant-builtin
aliases: ["jupyter", "live kernel", "notebook analysis"]
trigger_phrases: ["open a notebook workflow", "analyze this in jupyter", "use a live python kernel"]
keywords: ["jupyter", "notebook", "analysis", "kernel", "python", "data science"]
category: data-science
---

# Jupyter Live Kernel

Use this built-in skill when the user wants interactive notebook analysis, exploratory data work, or a live kernel workflow.

## Core rules

- Confirm the runtime, dataset location, and dependency posture before executing notebook cells.
- Keep exploratory work reproducible enough to replay outside the current kernel.
- Separate quick investigation from durable scripts, tests, or pipelines.
- Record assumptions about data freshness, sampling, and environment state.

## Default workflow

1. Inspect the data source, schema shape, and available runtime.
2. Load the smallest slice that can answer the question.
3. Iterate interactively while keeping cells and outputs interpretable.
4. Promote stable logic into scripts or documented procedures when the work becomes durable.

## Guardrails

- Do not hide environment-specific state inside unexplained notebook magic.
- Do not treat one kernel run as a reproducible result by default.
- Do not keep long-lived production logic trapped in ad hoc cells.
