---
name: Training
skill_id: training
description: Guides fine-tuning and post-training work with explicit data, objective, hardware, and rollback assumptions.
version: 1.0.0
source_kind: elephant-builtin
aliases: ["model training", "fine tuning", "post training"]
trigger_phrases: ["fine tune this model", "plan a training run", "set up post-training for this model"]
keywords: ["training", "fine-tuning", "post-training", "data", "objective", "checkpoint"]
category: mlops
---

# Training

Use this built-in skill when the user is planning or executing a fine-tuning, post-training, or model adaptation workflow.

## Core rules

- Start from the training objective and data posture, not the framework choice.
- Confirm hardware, checkpoint, tokenizer, and evaluation compatibility up front.
- Keep launch configs, dataset versions, and output checkpoints traceable.
- Treat rollback and validation as part of the training plan.

## Default workflow

1. Define the target behavior change and evaluation criteria.
2. Inspect dataset quality, formatting, and licensing constraints.
3. Choose the training path that matches the budget and hardware.
4. Validate checkpoints against the baseline before promoting them.

## Guardrails

- Do not launch expensive runs without a measurable success condition.
- Do not assume dataset quality from format alone.
- Do not promote a checkpoint that has not been evaluated against the baseline.
