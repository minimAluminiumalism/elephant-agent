"""Derive user profile display fields directly from PM facts (claims).

This replaces the legacy UserCardRecord. The dashboard and prompt
projection both call derive_profile_from_claims() to get structured
profile data from the single source of truth: active PM claims.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


# Maps topic → display field key.
# Topic keys follow the canonical four-lens schema:
#   identity.<facet>.<sub>  world.<facet>.<sub>  pulse.<facet>.<sub>  journey.<facet>.<sub>
TOPIC_TO_FIELD: dict[str, str] = {
    # identity lens
    "identity.anchor.name.preferred": "preferred_name",
    "identity.anchor.birth.date": "birth_date",
    "identity.anchor.gender.self_description": "gender",
    "identity.character.mbti.type": "mbti",
    "identity.style.hobbies.personal": "hobbies",
    "identity.style.language.first": "locale",
    "identity.style.companion.posture": "relationship_mode",
    "identity.body.history.trauma": "boundaries",
    # world lens
    "world.places.city.current": "current_city",
    # pulse lens
    "pulse.chapter.work.role": "current_work",
}

# Display labels for the dashboard profile panel.
FIELD_TO_LABEL: dict[str, str] = {
    "preferred_name": "Name",
    "current_city": "City",
    "birth_date": "Birth date",
    "gender": "Gender",
    "mbti": "MBTI",
    "hobbies": "Hobbies",
    "locale": "Speaks",
    "current_work": "Working on",
    "relationship_mode": "Relationship mode",
    "boundaries": "Boundaries",
}


def derive_profile_from_claims(facts: tuple[Any, ...] | list[Any]) -> dict[str, str]:
    """Extract structured profile fields from active PM facts.

    Returns a dict with keys matching the old user_card field names
    (preferred_name, current_city, etc.) so downstream code works unchanged.
    Only active claims are considered. First match per field wins.
    """
    profile: dict[str, str] = {}
    for fact in facts:
        if str(getattr(fact, "status", "") or "").strip() != "active":
            continue
        metadata = getattr(fact, "metadata", {})
        if not isinstance(metadata, Mapping):
            metadata = {}
        topic = str(metadata.get("topic") or "").strip()
        field = TOPIC_TO_FIELD.get(topic)
        if field and field not in profile:
            text = str(getattr(fact, "text", "") or "").strip()
            if text:
                profile[field] = text
    return profile


def render_profile_text_from_claims(facts: tuple[Any, ...] | list[Any]) -> str:
    """Render a natural-language profile summary for prompt injection.

    Used in the frozen prefix where the LLM needs a brief user context.
    """
    profile = derive_profile_from_claims(facts)
    if not profile:
        return ""
    lines: list[str] = []
    if profile.get("preferred_name"):
        lines.append(f"Name: {profile['preferred_name']}")
    if profile.get("locale"):
        lines.append(f"Language: {profile['locale']}")
    if profile.get("current_city"):
        lines.append(f"Location: {profile['current_city']}")
    if profile.get("current_work"):
        lines.append(f"Current focus: {profile['current_work']}")
    if profile.get("boundaries"):
        lines.append(f"Care context: {profile['boundaries']}")
    return "\n".join(lines)
