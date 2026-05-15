---
name: Find Nearby
skill_id: find-nearby
description: Find nearby places or services with location-aware search while keeping assumptions about distance, hours, and category explicit.
version: 1.0.0
source_kind: elephant-builtin
---

# Find Nearby

Use this skill when the user wants a nearby place, service, or activity rather than a generic web search result list.

## Preferred Flow

1. Confirm the location anchor first.
2. Search for the requested category with map-aware or review-aware sources.
3. Return a short, ranked shortlist with distance or area context.
4. Verify hours or open status if the user cares about going now.

## Guardrails

- Do not infer the user's live location without an explicit hint.
- Call out when a recommendation is only approximate.
