"""Ephemeral rendered state views derived from PM facts and State."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class RenderedUserProfileView:
    user_profile_id: str
    profile_id: str
    preferred_name: str | None = None
    locale: str | None = None
    timezone: str | None = None
    communication_preferences: tuple[str, ...] = ()
    boundaries: tuple[str, ...] = ()
    biography_fragments: tuple[str, ...] = ()
    durable_notes: tuple[str, ...] = ()
    shared_preferences: tuple[str, ...] = ()
    source_user_profile_path: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class RenderedRelationshipView:
    relationship_id: str
    profile_id: str
    elephant_id: str
    user_profile_id: str | None = None
    interaction_preferences: tuple[str, ...] = ()
    repair_history: tuple[str, ...] = ()
    trust_markers: tuple[str, ...] = ()
    expectations: tuple[str, ...] = ()
    local_corrections: tuple[str, ...] = ()
    continuity_notes: tuple[str, ...] = ()
    created_at: datetime | None = None
    updated_at: datetime | None = None
