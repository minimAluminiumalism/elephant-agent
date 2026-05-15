---
title: "Why Elephant Agent"
description: "Elephant Agent is a personal AI that grows a correctable Personal Model from claims, provenance, and useful questions."
---

# Why Elephant Agent

Elephant Agent begins from a simple belief:

> Personal AI should not ask you to become its memory. It should grow a
> correctable understanding of the path you are already walking.

Most agent systems still lose the thread in predictable ways. They can have a
long transcript, many tools, and even a memory feature, yet still fail to answer:
what should this agent reliably understand about the person it helps?

## The gap

| Common agent shape | What usually breaks | Elephant Agent's answer |
| --- | --- | --- |
| Stateless chat | Every session starts cold. | Durable elephants and wake/resume continuity. |
| Transcript memory | The system stores more text but understands less. | Active Personal Model claims with provenance. |
| Skill-first agent | Capability grows, but the person stays vague. | Skills orbit understanding instead of replacing it. |
| Hidden personalization | The user cannot see or correct what changed. | Claims, questions, and evidence stay inspectable. |
| Pushy autonomy | Proactive behavior becomes interruption. | Curiosity is visible, optional, and user-paced. |

## The core bet

Elephant Agent puts a **Personal Model** at the center. That model is not a
profile in the advertising sense. It is the current, correctable understanding
that helps future replies start from the right place.

```mermaid
flowchart LR
  transcript["Transcript"] --> evidence["Evidence"]
  evidence --> claims["Correctable claims"]
  claims --> prompt["Future prompt projection"]
  claims --> questions["Useful questions"]
  questions --> claims
```

The Personal Model is organized around four lenses:

| Lens | What it carries | Example shape |
| --- | --- | --- |
| **Identity** | Stable facts about who the person is and how to address them. | Name, language, role, boundaries. |
| **World** | People, projects, places, tools, and external context. | A repository, collaborator, team, or workspace. |
| **Pulse** | Current state, energy, priorities, and near-term pressure. | What is alive this week. |
| **Journey** | Longer arcs, decisions, lessons, and recurring patterns. | Why a direction changed, or what keeps returning. |

:::note
Memory is part of this system, but it is not the whole system. Recall can support
a current turn; it does not automatically become durable truth.
:::

## The public path

The supported path is intentionally small:

```bash
elephant init
elephant status
elephant wake
```

| Step | What happens | Why it matters |
| --- | --- | --- |
| `init` | Creates the first elephant and provider posture. | The relationship starts with identity and readiness. |
| `status` | Checks local runtime and model readiness. | The first real conversation starts from a known state. |
| `wake` | Opens the durable chat surface. | The same elephant can pick up the thread later. |

## What makes it different

Elephant Agent is not trying to win by having the longest transcript or the
largest tool shelf. It is trying to become **more yours over time**:

- it remembers through correctable claims, not opaque summaries
- it asks when a gap would improve future help
- it keeps silence honored when you do not answer
- it uses tools, skills, models, messaging, and jobs as visible capabilities
- it lets you inspect why a claim exists before you rely on it
