"""Persist canonical personal-AI records with ledger tracking."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
import hashlib
from uuid import uuid4

from .canonical import CanonicalPersonalModelRuntimeStateBundle
from .projection import render_user_card_profile_text
from packages.contracts import ElephantIdentityRecord, Fact, Record, RelationshipMemoryRecord, UserCardRecord
from packages.evidence import MemoryRuntime
from packages.storage import RuntimeStorageRepository


@dataclass(frozen=True, slots=True)
class PersistedCanonicalState:
    elephant_identity: object | None
    user_card: object | None
    relationship_memory: object | None


@dataclass(frozen=True, slots=True)
class StoredIdentityLedgerEntry:
    entry_id: str
    elephant_id: str
    profile_id: str
    action: str
    summary: str
    metadata: dict[str, str]
    created_at: datetime


@dataclass(frozen=True, slots=True)
class StoredUserCardLedgerEntry:
    entry_id: str
    user_card_id: str
    profile_id: str
    action: str
    summary: str
    metadata: dict[str, str]
    created_at: datetime


@dataclass(frozen=True, slots=True)
class StoredRelationshipLedgerEntry:
    entry_id: str
    relationship_id: str
    profile_id: str
    action: str
    summary: str
    metadata: dict[str, str]
    created_at: datetime


def load_persisted_canonical_state(repository: RuntimeStorageRepository, profile_id: str) -> PersistedCanonicalState:
    load_elephant_identity = getattr(repository, "load_elephant_identity_for_profile", None)
    load_user_card = getattr(repository, "load_user_card_for_profile", None)
    load_relationship_memory = getattr(repository, "load_relationship_memory_for_profile", None)
    if load_elephant_identity is None or load_user_card is None or load_relationship_memory is None:
        return _load_canonical_records(repository, profile_id)
    return PersistedCanonicalState(
        elephant_identity=load_elephant_identity(profile_id),
        user_card=load_user_card(profile_id),
        relationship_memory=load_relationship_memory(profile_id),
    )


def resolve_runtime_state(
    repository: RuntimeStorageRepository,
    *,
    state_id: str | None = None,
    episode_id: str | None = None,
    personal_model_id: str | None = None,
    elephant_id: str | None = None,
    state_anchor: str | None = None,
    status: str | None = "active",
    required: bool = False,
):
    explicit_state_id = str(state_id or "").strip()
    if explicit_state_id:
        state = repository.load_state(explicit_state_id)
        if state is not None:
            return state
    explicit_episode_id = str(episode_id or "").strip()
    if explicit_episode_id:
        stored_episode = repository.load_episode(explicit_episode_id)
        if stored_episode is not None:
            state = repository.load_state(stored_episode.state_id)
            if state is not None:
                return state
            if personal_model_id is None:
                personal_model_id = stored_episode.personal_model_id
    resolved_profile_id = str(personal_model_id or "").strip() or None
    resolved_elephant_id = str(elephant_id or "").strip() or None
    resolved_anchor = str(state_anchor or "").strip() or None
    states = repository.list_states(status=status) if status is not None else repository.list_states()
    if resolved_profile_id is not None:
        states = tuple(state for state in states if state.personal_model_id == resolved_profile_id)
    if resolved_anchor is not None:
        for state in states:
            if state.state_anchor == resolved_anchor:
                return state
    if resolved_elephant_id is not None:
        elephant_anchors = {resolved_elephant_id, f"elephant:{resolved_elephant_id}"}
        for state in states:
            if state.elephant_id == resolved_elephant_id or state.state_anchor in elephant_anchors:
                return state
    current = repository.current_state()
    if current is not None:
        if resolved_profile_id is not None and current.personal_model_id != resolved_profile_id:
            current = None
        if current is not None and resolved_anchor is not None and current.state_anchor != resolved_anchor:
            current = None
        if current is not None and resolved_elephant_id is not None and current.elephant_id != resolved_elephant_id and current.state_anchor not in {resolved_elephant_id, f"elephant:{resolved_elephant_id}"}:
            current = None
        if current is not None:
            return current
    if resolved_profile_id is not None and len(states) == 1:
        return states[0]
    if required:
        targets = ", ".join(
            candidate
            for candidate in (
                explicit_state_id,
                explicit_episode_id,
                resolved_anchor,
                resolved_elephant_id,
                resolved_profile_id or "",
            )
            if candidate
        ) or "runtime-state"
        raise KeyError(f"runtime state not found for {targets}")
    return None


def sync_canonical_profile_state(
    repository: RuntimeStorageRepository,
    bundle: CanonicalPersonalModelRuntimeStateBundle,
    *,
    previous: PersistedCanonicalState,
    sync_source: str,
    memory_runtime: MemoryRuntime | None = None,
    surface: str = "",
    state_id: str | None = None,
    episode_id: str | None = None,
    user_directed: bool = True,
) -> PersistedCanonicalState:
    synced_at = datetime.now(timezone.utc)
    profile_id = bundle.elephant_identity.profile_id
    if memory_runtime is not None:
        _capture_canonical_profile_updates(
            repository,
            bundle,
            previous=previous,
            sync_source=sync_source,
            surface=surface,
            state_id=state_id,
            episode_id=episode_id,
            user_directed=user_directed,
            captured_at=synced_at,
        )
    upsert_elephant_identity = getattr(repository, "upsert_elephant_identity", None)
    upsert_user_card = getattr(repository, "upsert_user_card", None)
    upsert_relationship_memory = getattr(repository, "upsert_relationship_memory", None)
    append_identity_ledger = getattr(repository, "append_identity_ledger", None)
    append_user_card_ledger = getattr(repository, "append_user_card_ledger", None)
    append_relationship_ledger = getattr(repository, "append_relationship_ledger", None)
    if (
        upsert_elephant_identity is None
        or upsert_user_card is None
        or upsert_relationship_memory is None
    ):
        _upsert_canonical_records(repository, bundle, synced_at=synced_at)
        return _load_canonical_records(repository, profile_id)
    upsert_elephant_identity(bundle.elephant_identity, updated_at=synced_at)
    upsert_user_card(bundle.user_card, updated_at=synced_at)
    upsert_relationship_memory(bundle.relationship_memory, updated_at=synced_at)
    metadata = {
        "profile_id": profile_id,
        "sync_source": sync_source,
    }
    if bundle.elephant_identity.source_manifest_path is not None:
        metadata["manifest_path"] = bundle.elephant_identity.source_manifest_path
    if bundle.elephant_identity.source_elephant_path is not None:
        metadata["elephant_path"] = bundle.elephant_identity.source_elephant_path
    if bundle.user_card.source_user_profile_path is not None:
        metadata["user_profile_path"] = bundle.user_card.source_user_profile_path
    if _record_changed(previous.elephant_identity, bundle.elephant_identity) and append_identity_ledger is not None:
        append_identity_ledger(
            StoredIdentityLedgerEntry(
                entry_id=f"identity:{uuid4().hex}",
                elephant_id=bundle.elephant_identity.elephant_id,
                profile_id=profile_id,
                action="canonical_sync",
                summary=f"synchronized canonical elephant identity from {sync_source}",
                metadata={**metadata, "owner": "elephant"},
                created_at=synced_at,
            )
        )
    if _record_changed(previous.user_card, bundle.user_card) and append_user_card_ledger is not None:
        append_user_card_ledger(
            StoredUserCardLedgerEntry(
                entry_id=f"user-card:{uuid4().hex}",
                user_card_id=bundle.user_card.user_card_id,
                profile_id=profile_id,
                action="canonical_sync",
                summary=f"synchronized canonical user card from {sync_source}",
                metadata={**metadata, "owner": "user"},
                created_at=synced_at,
            )
        )
    if _record_changed(previous.relationship_memory, bundle.relationship_memory) and append_relationship_ledger is not None:
        append_relationship_ledger(
            StoredRelationshipLedgerEntry(
                entry_id=f"relationship:{uuid4().hex}",
                relationship_id=bundle.relationship_memory.relationship_id,
                profile_id=profile_id,
                action="canonical_sync",
                summary=f"synchronized canonical relationship memory from {sync_source}",
                metadata={**metadata, "owner": "relationship"},
                created_at=synced_at,
            )
        )
    return load_persisted_canonical_state(repository, profile_id)


def _capture_canonical_profile_updates(
    repository: RuntimeStorageRepository,
    bundle: CanonicalPersonalModelRuntimeStateBundle,
    *,
    previous: PersistedCanonicalState,
    sync_source: str,
    surface: str,
    state_id: str | None,
    episode_id: str | None,
    user_directed: bool,
    captured_at: datetime,
) -> None:
    profile_id = bundle.elephant_identity.profile_id
    upsert_fact = getattr(repository, "upsert_personal_model_fact", None)
    if not callable(upsert_fact):
        raise RuntimeError("canonical personal-model fact writes require fact-backed storage")
    component_specs = (
        (
            "user-card",
            previous.user_card,
            bundle.user_card,
            "user_profile",
            "identity",
            "identity.anchor.user_card",
            _user_card_capture_content(bundle.user_card),
            "low",
        ),
        (
            "relationship-memory",
            previous.relationship_memory,
            bundle.relationship_memory,
            "relationship_memory",
            "identity",
            "identity.style.relationship_memory",
            _relationship_capture_content(bundle.relationship_memory),
            "medium",
        ),
    )
    for component, prior_record, current_record, component_kind, lens, topic, content, sensitivity in component_specs:
        if not _record_changed(prior_record, current_record):
            continue
        if not content.strip():
            continue
        upsert_fact(
            Fact(
                fact_id=_canonical_update_fact_id(profile_id, component),
                personal_model_id=profile_id,
                lens=lens,
                text=content,
                confidence=1.0 if user_directed else 0.72,
                committed_at=captured_at,
                source="user_explicit" if user_directed else "pm_agent_promote",
                source_episode_ids=(episode_id,) if episode_id else (),
                status="active",
                metadata={
                    "topic": topic,
                    "component_kind": component_kind,
                    "canonical_component": component,
                    "sync_source": sync_source,
                    "surface": surface,
                    "state_id": state_id or "",
                    "episode_id": episode_id or "",
                    "sensitivity": sensitivity,
                    "user_directed": "true" if user_directed else "false",
                    "recall_policy": "stable",
                    "memory_lifecycle": "durable",
                },
            )
        )


def _canonical_update_fact_id(profile_id: str, component: str) -> str:
    digest = hashlib.sha256(f"{profile_id}:{component}".encode("utf-8")).hexdigest()[:16]
    return f"fact:canonical:{component}:{digest}"


def _canonical_component_payload(record: object | None) -> dict[str, object] | None:
    if record is None:
        return None
    if isinstance(record, ElephantIdentityRecord):
        return _elephant_identity_payload(record)
    if isinstance(record, UserCardRecord):
        return _user_card_payload(record)
    if isinstance(record, RelationshipMemoryRecord):
        return _relationship_memory_payload(record)
    return None


def _identity_capture_content(record: ElephantIdentityRecord) -> str:
    parts = [
        f"Display name: {record.display_name}",
        f"Identity mode: {record.identity_mode}",
        f"Personality preset: {record.personality_preset}",
        f"Initiative: {record.initiative}",
        f"Relational stance: {record.relational_stance}",
        f"Working style contract: {record.working_style_contract}",
    ]
    if record.elephant_identity_text:
        parts.append(f"Elephant identity text: {record.elephant_identity_text}")
    return "\n".join(part for part in parts if part.strip())


def _user_card_capture_content(record: UserCardRecord) -> str:
    rendered = render_user_card_profile_text(record)
    if rendered is not None and rendered.strip():
        return rendered
    parts = [
        f"Preferred name: {record.preferred_name or ''}".strip(),
        *(f"Biography: {item}" for item in record.biography_fragments if item.strip()),
        *(f"Boundary: {item}" for item in record.boundaries if item.strip()),
        *(f"Remember: {item}" for item in record.durable_notes if item.strip()),
    ]
    return "\n".join(part for part in parts if part.strip())


_SYSTEM_RELATIONSHIP_PREFERENCES = frozenset(
    {
        "text-first",
        "preserve-relationship-timeline",
        "preserve-preferences",
        "preserve-corrections",
        "preserve-emotional-context",
    }
)
_SYSTEM_RELATIONSHIP_EXPECTATION_PREFIXES = (
    "initiative:",
    "relational_stance:",
    "personality_label:",
)


def _relationship_capture_content(record: RelationshipMemoryRecord) -> str:
    user_preferences = tuple(
        item.strip()
        for item in record.interaction_preferences
        if item.strip() and item.strip() not in _SYSTEM_RELATIONSHIP_PREFERENCES
    )
    user_expectations = tuple(
        item.strip()
        for item in record.expectations
        if item.strip()
        and not any(
            item.strip().startswith(prefix)
            for prefix in _SYSTEM_RELATIONSHIP_EXPECTATION_PREFIXES
        )
    )
    parts = [
        *(f"Interaction preference: {item}" for item in user_preferences),
        *(f"Expectation: {item}" for item in user_expectations),
        *(f"Trust marker: {item}" for item in record.trust_markers if item.strip()),
        *(f"Repair history: {item}" for item in record.repair_history if item.strip()),
        *(f"Local correction: {item}" for item in record.local_corrections if item.strip()),
        *(f"Continuity note: {item}" for item in record.continuity_notes if item.strip()),
    ]
    return "\n".join(part for part in parts if part.strip())


def _record_changed(previous, current) -> bool:
    if previous is None:
        return True
    return replace(previous, created_at=None, updated_at=None) != replace(
        current,
        created_at=None,
        updated_at=None,
    )


def _record_id(profile_id: str, component: str) -> str:
    return f"profile:{profile_id}:{component}"


def _tuple_payload(value: object) -> tuple[str, ...]:
    if isinstance(value, (list, tuple)):
        return tuple(str(item) for item in value if str(item))
    return ()


def _datetime_payload(value: object) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    try:
        parsed = datetime.fromisoformat(str(value))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed


def _load_canonical_records(repository: RuntimeStorageRepository, profile_id: str) -> PersistedCanonicalState:
    identity_record = repository.load_record(_record_id(profile_id, "state-identity"))
    user_record = repository.load_record(_record_id(profile_id, "user-card"))
    relationship_record = repository.load_record(_record_id(profile_id, "relationship-memory"))
    return PersistedCanonicalState(
        elephant_identity=_elephant_identity_from_record(identity_record),
        user_card=_user_card_from_record(user_record),
        relationship_memory=_relationship_memory_from_record(relationship_record),
    )


def _upsert_canonical_records(
    repository: RuntimeStorageRepository,
    bundle: CanonicalPersonalModelRuntimeStateBundle,
    *,
    synced_at: datetime,
) -> None:
    profile_id = bundle.elephant_identity.profile_id
    personal_model = repository.ensure_default_personal_model()
    state_id = _sync_elephant_identity(repository, bundle.elephant_identity, synced_at=synced_at)
    _upsert_component_record(
        repository,
        component="state-identity",
        profile_id=profile_id,
        schema_version="elephant_identity/v1",
        layer_type="elephant_identity",
        payload=_elephant_identity_payload(bundle.elephant_identity),
        synced_at=synced_at,
        owner_scope="state" if state_id is not None else None,
        state_id=state_id,
        personal_model_id=None,
    )
    _upsert_component_record(
        repository,
        component="user-card",
        profile_id=profile_id,
        schema_version="user_card/v1",
        layer_type="user_card",
        payload=_user_card_payload(bundle.user_card),
        synced_at=synced_at,
        owner_scope="personal_model",
        state_id=None,
        personal_model_id=personal_model.personal_model_id,
    )
    _upsert_component_record(
        repository,
        component="relationship-memory",
        profile_id=profile_id,
        schema_version="relationship_memory/v1",
        layer_type="relationship_memory",
        payload=_relationship_memory_payload(bundle.relationship_memory),
        synced_at=synced_at,
        owner_scope="personal_model",
        state_id=None,
        personal_model_id=personal_model.personal_model_id,
    )


def _sync_elephant_identity(
    repository: RuntimeStorageRepository,
    identity: ElephantIdentityRecord,
    *,
    synced_at: datetime,
) -> str | None:
    for state in repository.list_states():
        if state.elephant_id != identity.elephant_id:
            continue
        repository.upsert_state(
            replace(
                state,
                elephant_name=identity.display_name,
                identity_mode=identity.identity_mode,
                initiative=identity.initiative,
                posture=identity.relational_stance,
                working_style=identity.working_style_contract or identity.personality_preset,
                elephant_identity_text=identity.elephant_identity_text or state.elephant_identity_text,
                source_manifest=identity.source_manifest_path or state.source_manifest,
                metadata={**dict(state.metadata), "profile_id": identity.profile_id},
            ),
            updated_at=synced_at,
        )
        return state.state_id
    return None


def _upsert_component_record(
    repository: RuntimeStorageRepository,
    *,
    component: str,
    profile_id: str,
    schema_version: str,
    layer_type: str,
    payload: dict[str, object],
    synced_at: datetime,
    owner_scope: str | None,
    state_id: str | None,
    personal_model_id: str | None,
) -> None:
    record_id = _record_id(profile_id, component)
    existing = repository.load_record(record_id)
    repository.upsert_record(
        Record(
            record_id=record_id,
            kind="layer",
            schema_version=schema_version,
            owner_scope=owner_scope,
            personal_model_id=personal_model_id,
            state_id=state_id,
            layer_type=layer_type,
            payload=payload,
            created_at=existing.created_at if existing is not None else synced_at,
            metadata={
                "profile_id": profile_id,
                "component": component,
            },
        )
    )


def _elephant_identity_payload(record: ElephantIdentityRecord) -> dict[str, object]:
    return {
        "elephant_id": record.elephant_id,
        "profile_id": record.profile_id,
        "display_name": record.display_name,
        "identity_mode": record.identity_mode,
        "personality_preset": record.personality_preset,
        "initiative": record.initiative,
        "relational_stance": record.relational_stance,
        "working_style_contract": record.working_style_contract,
        "elephant_identity_text": record.elephant_identity_text,
        "governance_flags": list(record.governance_flags),
        "source_manifest_path": record.source_manifest_path,
        "source_elephant_path": record.source_elephant_path,
        "created_at": record.created_at.isoformat() if record.created_at is not None else None,
        "updated_at": record.updated_at.isoformat() if record.updated_at is not None else None,
    }


def _user_card_payload(record: UserCardRecord) -> dict[str, object]:
    return {
        "user_card_id": record.user_card_id,
        "profile_id": record.profile_id,
        "preferred_name": record.preferred_name,
        "locale": record.locale,
        "timezone": record.timezone,
        "communication_preferences": list(record.communication_preferences),
        "boundaries": list(record.boundaries),
        "biography_fragments": list(record.biography_fragments),
        "durable_notes": list(record.durable_notes),
        "shared_preferences": list(record.shared_preferences),
        "source_user_profile_path": record.source_user_profile_path,
        "created_at": record.created_at.isoformat() if record.created_at is not None else None,
        "updated_at": record.updated_at.isoformat() if record.updated_at is not None else None,
    }


def _relationship_memory_payload(record: RelationshipMemoryRecord) -> dict[str, object]:
    return {
        "relationship_id": record.relationship_id,
        "profile_id": record.profile_id,
        "elephant_id": record.elephant_id,
        "user_card_id": record.user_card_id,
        "interaction_preferences": list(record.interaction_preferences),
        "repair_history": list(record.repair_history),
        "trust_markers": list(record.trust_markers),
        "expectations": list(record.expectations),
        "local_corrections": list(record.local_corrections),
        "continuity_notes": list(record.continuity_notes),
        "created_at": record.created_at.isoformat() if record.created_at is not None else None,
        "updated_at": record.updated_at.isoformat() if record.updated_at is not None else None,
    }


def _elephant_identity_from_record(record: Record | None) -> ElephantIdentityRecord | None:
    if record is None or record.schema_version != "elephant_identity/v1":
        return None
    payload = dict(record.payload)
    return ElephantIdentityRecord(
        elephant_id=str(payload.get("elephant_id") or ""),
        profile_id=str(payload.get("profile_id") or ""),
        display_name=str(payload.get("display_name") or ""),
        identity_mode=str(payload.get("identity_mode") or ""),
        personality_preset=str(payload.get("personality_preset") or ""),
        initiative=str(payload.get("initiative") or ""),
        relational_stance=str(payload.get("relational_stance") or ""),
        working_style_contract=str(payload.get("working_style_contract") or ""),
        elephant_identity_text=str(payload["elephant_identity_text"]) if payload.get("elephant_identity_text") is not None else None,
        governance_flags=_tuple_payload(payload.get("governance_flags")),
        source_manifest_path=str(payload["source_manifest_path"]) if payload.get("source_manifest_path") is not None else None,
        source_elephant_path=str(payload["source_elephant_path"]) if payload.get("source_elephant_path") is not None else None,
        created_at=_datetime_payload(payload.get("created_at")),
        updated_at=_datetime_payload(payload.get("updated_at")),
    )


def _user_card_from_record(record: Record | None) -> UserCardRecord | None:
    if record is None or record.schema_version != "user_card/v1":
        return None
    payload = dict(record.payload)
    return UserCardRecord(
        user_card_id=str(payload.get("user_card_id") or ""),
        profile_id=str(payload.get("profile_id") or ""),
        preferred_name=str(payload["preferred_name"]) if payload.get("preferred_name") is not None else None,
        locale=str(payload["locale"]) if payload.get("locale") is not None else None,
        timezone=str(payload["timezone"]) if payload.get("timezone") is not None else None,
        communication_preferences=_tuple_payload(payload.get("communication_preferences")),
        boundaries=_tuple_payload(payload.get("boundaries")),
        biography_fragments=_tuple_payload(payload.get("biography_fragments")),
        durable_notes=_tuple_payload(payload.get("durable_notes")),
        shared_preferences=_tuple_payload(payload.get("shared_preferences")),
        source_user_profile_path=str(payload["source_user_profile_path"]) if payload.get("source_user_profile_path") is not None else None,
        created_at=_datetime_payload(payload.get("created_at")),
        updated_at=_datetime_payload(payload.get("updated_at")),
    )


def _relationship_memory_from_record(record: Record | None) -> RelationshipMemoryRecord | None:
    if record is None or record.schema_version != "relationship_memory/v1":
        return None
    payload = dict(record.payload)
    return RelationshipMemoryRecord(
        relationship_id=str(payload.get("relationship_id") or ""),
        profile_id=str(payload.get("profile_id") or ""),
        elephant_id=str(payload.get("elephant_id") or ""),
        user_card_id=str(payload["user_card_id"]) if payload.get("user_card_id") is not None else None,
        interaction_preferences=_tuple_payload(payload.get("interaction_preferences")),
        repair_history=_tuple_payload(payload.get("repair_history")),
        trust_markers=_tuple_payload(payload.get("trust_markers")),
        expectations=_tuple_payload(payload.get("expectations")),
        local_corrections=_tuple_payload(payload.get("local_corrections")),
        continuity_notes=_tuple_payload(payload.get("continuity_notes")),
        created_at=_datetime_payload(payload.get("created_at")),
        updated_at=_datetime_payload(payload.get("updated_at")),
    )
