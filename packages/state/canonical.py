"""Canonical identity, user, and relationship builders for loaded profiles."""

from __future__ import annotations

from dataclasses import dataclass

from packages.contracts import ElephantIdentityRecord, PersonalModelRecordBundle, RelationshipMemoryRecord, UserCardRecord
from packages.storage.repository_support import canonical_personal_model_id

from .governance import (
    build_companion_identity_state,
    parse_user_profile_content,
    resolved_companion_settings,
    user_biography_field_ids,
)
from .loader import LoadedProfile


@dataclass(frozen=True, slots=True)
class CanonicalProfileIds:
    elephant_id: str
    user_card_id: str
    relationship_id: str


@dataclass(frozen=True, slots=True)
class CanonicalPersonalModelRuntimeStateBundle:
    personal_model_record_bundle: PersonalModelRecordBundle
    elephant_identity: ElephantIdentityRecord
    user_card: UserCardRecord
    relationship_memory: RelationshipMemoryRecord


def canonical_profile_ids(profile_id: str) -> CanonicalProfileIds:
    normalized = canonical_personal_model_id(profile_id)
    return CanonicalProfileIds(
        elephant_id=f"{normalized}:elephant",
        user_card_id=f"{normalized}:user-card",
        relationship_id=f"{normalized}:relationship",
    )


def build_canonical_profile_state(
    profile: LoadedProfile,
    *,
    elephant_id: str | None = None,
    user_card_id: str | None = None,
    relationship_id: str | None = None,
) -> CanonicalPersonalModelRuntimeStateBundle:
    ids = canonical_profile_ids(profile.state.profile_id)
    resolved_elephant_id = elephant_id or ids.elephant_id
    resolved_user_card_id = user_card_id or ids.user_card_id
    resolved_relationship_id = relationship_id or ids.relationship_id
    elephant_identity = build_elephant_identity_record(profile, elephant_id=resolved_elephant_id)
    user_card = build_user_card_record(profile, user_card_id=resolved_user_card_id)
    relationship_memory = build_relationship_memory_record(
        profile,
        elephant_id=resolved_elephant_id,
        user_card_id=resolved_user_card_id,
        relationship_id=resolved_relationship_id,
    )
    return CanonicalPersonalModelRuntimeStateBundle(
        personal_model_record_bundle=build_personal_model_record_bundle(
            profile,
            elephant_identity=elephant_identity,
            user_card=user_card,
            relationship_memory=relationship_memory,
        ),
        elephant_identity=elephant_identity,
        user_card=user_card,
        relationship_memory=relationship_memory,
    )


def build_personal_model_record_bundle(
    profile: LoadedProfile,
    *,
    elephant_identity: ElephantIdentityRecord | None = None,
    user_card: UserCardRecord | None = None,
    relationship_memory: RelationshipMemoryRecord | None = None,
) -> PersonalModelRecordBundle:
    resolved_elephant_identity = elephant_identity or build_elephant_identity_record(profile)
    resolved_user_card = user_card or build_user_card_record(profile)
    resolved_relationship_memory = relationship_memory or build_relationship_memory_record(
        profile,
        elephant_id=resolved_elephant_identity.elephant_id,
        user_card_id=resolved_user_card.user_card_id,
    )
    return PersonalModelRecordBundle(
        profile=profile.state,
        elephant_identity=resolved_elephant_identity,
        user_card=resolved_user_card,
        relationship_memory=resolved_relationship_memory,
    )


def build_elephant_identity_record(
    profile: LoadedProfile,
    *,
    elephant_id: str | None = None,
) -> ElephantIdentityRecord:
    identity = build_companion_identity_state(profile)
    companion = resolved_companion_settings(profile)
    ids = canonical_profile_ids(profile.state.profile_id)
    return ElephantIdentityRecord(
        elephant_id=elephant_id or ids.elephant_id,
        profile_id=profile.state.profile_id,
        display_name=identity.display_name,
        identity_mode=identity.mode,
        personality_preset=identity.personality_preset,
        initiative=identity.initiative,
        relational_stance=identity.relational_stance,
        working_style_contract=identity.personality_summary,
        elephant_identity_text=_strip_or_none(profile.elephant_identity_text),
        governance_flags=_governance_flags(companion),
        source_manifest_path=profile.manifest_path,
        source_elephant_path=profile.state.elephant_path,
    )


def build_user_card_record(
    profile: LoadedProfile,
    *,
    user_card_id: str | None = None,
) -> UserCardRecord:
    parsed_profile = parse_user_profile_content(profile.user_profile_text or "")
    fields = dict(parsed_profile.field_values)
    locale = _strip_or_none(str(profile.manifest.get("locale") or ""))
    timezone = _strip_or_none(str(profile.manifest.get("timezone") or ""))
    communication_preferences, shared_preferences = _split_profile_preferences(profile.state.preferences)
    biography_fragments = _biography_fragments(fields)
    boundaries = _maybe_singleton(fields.get("boundaries"))
    ids = canonical_profile_ids(profile.state.profile_id)
    return UserCardRecord(
        user_card_id=user_card_id or ids.user_card_id,
        profile_id=profile.state.profile_id,
        preferred_name=_strip_or_none(fields.get("preferred_name")),
        locale=locale,
        timezone=timezone,
        communication_preferences=communication_preferences,
        boundaries=boundaries,
        biography_fragments=biography_fragments,
        durable_notes=parsed_profile.durable_notes,
        shared_preferences=shared_preferences,
        source_user_profile_path=profile.user_profile_path,
    )


def build_relationship_memory_record(
    profile: LoadedProfile,
    *,
    elephant_id: str | None = None,
    user_card_id: str | None = None,
    relationship_id: str | None = None,
) -> RelationshipMemoryRecord:
    ids = canonical_profile_ids(profile.state.profile_id)
    companion = resolved_companion_settings(profile)
    identity = build_companion_identity_state(profile)
    return RelationshipMemoryRecord(
        relationship_id=relationship_id or ids.relationship_id,
        profile_id=profile.state.profile_id,
        elephant_id=elephant_id or ids.elephant_id,
        user_card_id=user_card_id or ids.user_card_id,
        interaction_preferences=_interaction_preferences(companion),
        expectations=(
            f"initiative:{companion.initiative}",
            f"relational_stance:{identity.relational_stance}",
            f"personality_label:{identity.personality_label}",
        ),
        continuity_notes=tuple(note.strip() for note in companion.notes if note.strip()),
    )


def _governance_flags(companion) -> tuple[str, ...]:
    flags = [
        "text-first" if companion.text_first else "voice-capable",
        "preserve-relationship-timeline" if companion.preserve_relationship_timeline else "limit-relationship-timeline",
        "preserve-preferences" if companion.preserve_preferences else "limit-preferences",
        "preserve-corrections" if companion.preserve_corrections else "limit-corrections",
        "preserve-emotional-context" if companion.preserve_emotional_context else "limit-emotional-context",
    ]
    return tuple(flags)


def _interaction_preferences(companion) -> tuple[str, ...]:
    return _governance_flags(companion)


def _split_profile_preferences(values: tuple[str, ...]) -> tuple[tuple[str, ...], tuple[str, ...]]:
    communication: list[str] = []
    shared: list[str] = []
    for value in values:
        normalized = value.strip()
        if not normalized:
            continue
        if normalized.startswith(("tone:", "verbosity:", "language:", "response-style:")):
            communication.append(normalized)
        else:
            shared.append(normalized)
    return tuple(communication), tuple(shared)


def _biography_fragments(fields: dict[str, str]) -> tuple[str, ...]:
    fragments: list[str] = []
    for key in user_biography_field_ids(fields):
        value = _strip_or_none(fields.get(key))
        if value is not None:
            fragments.append(f"{key}:{value}")
    return tuple(fragments)


def _maybe_singleton(value: str | None) -> tuple[str, ...]:
    cleaned = _strip_or_none(value)
    if cleaned is None:
        return ()
    return (cleaned,)


def _strip_or_none(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


__all__ = [
    "CanonicalProfileIds",
    "CanonicalPersonalModelRuntimeStateBundle",
    "build_canonical_profile_state",
    "build_elephant_identity_record",
    "build_relationship_memory_record",
    "build_user_card_record",
    "canonical_profile_ids",
]
