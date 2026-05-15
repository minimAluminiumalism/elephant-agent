---
name: Webhook Subscriptions
skill_id: webhook-subscriptions
description: Guides webhook-driven integrations, event receivers, and trigger flows without inventing runtime support the current repo does not actually have.
version: 1.0.0
source_kind: elephant-builtin
aliases: ["webhooks", "webhook subscriptions", "event triggers"]
trigger_phrases: ["set up a webhook", "subscribe to events", "debug this webhook flow"]
keywords: ["webhook", "events", "integration", "trigger", "idempotency", "delivery"]
category: devops
---

# Webhook Subscriptions

Use this built-in skill when the user needs an inbound event flow, webhook receiver, or subscription-style integration.

## Core rules

- Start from the actual service contract, auth model, and delivery guarantees.
- Make idempotency, retry behavior, and signature verification explicit.
- Keep secrets and trust boundaries operator-owned.
- Distinguish planning a webhook surface from claiming a product feature already exists.

## Default workflow

1. Identify the producer, event schema, and expected consumer action.
2. Verify the receiver endpoint, auth mechanism, and validation path.
3. Define replay, retry, dedupe, and observability behavior.
4. Test with representative payloads before treating the integration as reliable.

## Guardrails

- Do not invent a webhook platform that the repo does not implement.
- Do not skip auth, replay protection, or delivery failure handling.
- Do not blur event ingestion, business action, and operator notification into one opaque step.
