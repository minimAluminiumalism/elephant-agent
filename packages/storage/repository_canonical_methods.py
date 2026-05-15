"""Repository methods for first-class canonical Personal Model state."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from typing import Sequence

from packages.contracts import ElephantIdentityRecord, RelationshipMemoryRecord, UserCardRecord

from .repository_support import _iso, canonical_personal_model_id


def _json_list_text(values: Sequence[str]) -> str:
    return json.dumps(list(values), ensure_ascii=False, separators=(",", ":"))


def _parse_json_list(raw: str | None) -> tuple[str, ...]:
    if not raw:
        return ()
    try:
        value = json.loads(raw)
    except json.JSONDecodeError:
        return ()
    if not isinstance(value, list):
        return ()
    return tuple(str(item) for item in value)


def _parse_datetime(raw: str | None) -> datetime | None:
    if not raw:
        return None
    parsed = datetime.fromisoformat(raw)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed


def upsert_elephant_identity(self, record: ElephantIdentityRecord, *, updated_at: datetime | None = None) -> None:
    profile_id = canonical_personal_model_id(record.profile_id)
    timestamp = _iso(updated_at)
    created_at = _iso(record.created_at) if record.created_at is not None else timestamp
    updated = _iso(record.updated_at) if record.updated_at is not None else timestamp
    with self.connection() as connection:
        existing = connection.execute(
            "SELECT created_at FROM canonical_elephant_identities WHERE profile_id = ?",
            (profile_id,),
        ).fetchone()
        if existing is not None:
            created_at = str(existing["created_at"])
        connection.execute(
            """
            INSERT INTO canonical_elephant_identities (
                profile_id, elephant_id, display_name, identity_mode, personality_preset,
                initiative, relational_stance, working_style_contract,
                elephant_identity_text, governance_flags_json, source_manifest_path,
                source_elephant_path, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(profile_id) DO UPDATE SET
                elephant_id = excluded.elephant_id,
                display_name = excluded.display_name,
                identity_mode = excluded.identity_mode,
                personality_preset = excluded.personality_preset,
                initiative = excluded.initiative,
                relational_stance = excluded.relational_stance,
                working_style_contract = excluded.working_style_contract,
                elephant_identity_text = excluded.elephant_identity_text,
                governance_flags_json = excluded.governance_flags_json,
                source_manifest_path = excluded.source_manifest_path,
                source_elephant_path = excluded.source_elephant_path,
                updated_at = excluded.updated_at
            """,
            (
                profile_id,
                record.elephant_id,
                record.display_name,
                record.identity_mode,
                record.personality_preset,
                record.initiative,
                record.relational_stance,
                record.working_style_contract,
                record.elephant_identity_text,
                _json_list_text(record.governance_flags),
                record.source_manifest_path,
                record.source_elephant_path,
                created_at,
                updated,
            ),
        )
        connection.commit()


def load_elephant_identity_for_profile(self, profile_id: str) -> ElephantIdentityRecord | None:
    canonical_id = canonical_personal_model_id(profile_id)
    with self.connection() as connection:
        row = connection.execute(
            "SELECT * FROM canonical_elephant_identities WHERE profile_id = ?",
            (canonical_id,),
        ).fetchone()
    if row is None:
        return None
    return ElephantIdentityRecord(
        elephant_id=row["elephant_id"],
        profile_id=row["profile_id"],
        display_name=row["display_name"],
        identity_mode=row["identity_mode"],
        personality_preset=row["personality_preset"],
        initiative=row["initiative"],
        relational_stance=row["relational_stance"],
        working_style_contract=row["working_style_contract"],
        elephant_identity_text=row["elephant_identity_text"],
        governance_flags=_parse_json_list(row["governance_flags_json"]),
        source_manifest_path=row["source_manifest_path"],
        source_elephant_path=row["source_elephant_path"],
        created_at=_parse_datetime(row["created_at"]),
        updated_at=_parse_datetime(row["updated_at"]),
    )


def upsert_user_card(self, record: UserCardRecord, *, updated_at: datetime | None = None) -> None:
    profile_id = canonical_personal_model_id(record.profile_id)
    timestamp = _iso(updated_at)
    created_at = _iso(record.created_at) if record.created_at is not None else timestamp
    updated = _iso(record.updated_at) if record.updated_at is not None else timestamp
    with self.connection() as connection:
        existing = connection.execute(
            "SELECT created_at FROM canonical_user_cards WHERE profile_id = ?",
            (profile_id,),
        ).fetchone()
        if existing is not None:
            created_at = str(existing["created_at"])
        connection.execute(
            """
            INSERT INTO canonical_user_cards (
                profile_id, user_card_id, preferred_name, locale, timezone,
                communication_preferences_json, boundaries_json,
                biography_fragments_json, durable_notes_json,
                shared_preferences_json, source_user_profile_path,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(profile_id) DO UPDATE SET
                user_card_id = excluded.user_card_id,
                preferred_name = excluded.preferred_name,
                locale = excluded.locale,
                timezone = excluded.timezone,
                communication_preferences_json = excluded.communication_preferences_json,
                boundaries_json = excluded.boundaries_json,
                biography_fragments_json = excluded.biography_fragments_json,
                durable_notes_json = excluded.durable_notes_json,
                shared_preferences_json = excluded.shared_preferences_json,
                source_user_profile_path = excluded.source_user_profile_path,
                updated_at = excluded.updated_at
            """,
            (
                profile_id,
                record.user_card_id,
                record.preferred_name,
                record.locale,
                record.timezone,
                _json_list_text(record.communication_preferences),
                _json_list_text(record.boundaries),
                _json_list_text(record.biography_fragments),
                _json_list_text(record.durable_notes),
                _json_list_text(record.shared_preferences),
                record.source_user_profile_path,
                created_at,
                updated,
            ),
        )
        connection.commit()


def load_user_card_for_profile(self, profile_id: str) -> UserCardRecord | None:
    canonical_id = canonical_personal_model_id(profile_id)
    with self.connection() as connection:
        row = connection.execute(
            "SELECT * FROM canonical_user_cards WHERE profile_id = ?",
            (canonical_id,),
        ).fetchone()
    if row is None:
        return None
    return UserCardRecord(
        user_card_id=row["user_card_id"],
        profile_id=row["profile_id"],
        preferred_name=row["preferred_name"],
        locale=row["locale"],
        timezone=row["timezone"],
        communication_preferences=_parse_json_list(row["communication_preferences_json"]),
        boundaries=_parse_json_list(row["boundaries_json"]),
        biography_fragments=_parse_json_list(row["biography_fragments_json"]),
        durable_notes=_parse_json_list(row["durable_notes_json"]),
        shared_preferences=_parse_json_list(row["shared_preferences_json"]),
        source_user_profile_path=row["source_user_profile_path"],
        created_at=_parse_datetime(row["created_at"]),
        updated_at=_parse_datetime(row["updated_at"]),
    )


def upsert_relationship_memory(self, record: RelationshipMemoryRecord, *, updated_at: datetime | None = None) -> None:
    profile_id = canonical_personal_model_id(record.profile_id)
    timestamp = _iso(updated_at)
    created_at = _iso(record.created_at) if record.created_at is not None else timestamp
    updated = _iso(record.updated_at) if record.updated_at is not None else timestamp
    with self.connection() as connection:
        existing = connection.execute(
            "SELECT created_at FROM canonical_relationship_memories WHERE profile_id = ?",
            (profile_id,),
        ).fetchone()
        if existing is not None:
            created_at = str(existing["created_at"])
        connection.execute(
            """
            INSERT INTO canonical_relationship_memories (
                profile_id, relationship_id, elephant_id, user_card_id,
                interaction_preferences_json, repair_history_json,
                trust_markers_json, expectations_json, local_corrections_json,
                continuity_notes_json, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(profile_id) DO UPDATE SET
                relationship_id = excluded.relationship_id,
                elephant_id = excluded.elephant_id,
                user_card_id = excluded.user_card_id,
                interaction_preferences_json = excluded.interaction_preferences_json,
                repair_history_json = excluded.repair_history_json,
                trust_markers_json = excluded.trust_markers_json,
                expectations_json = excluded.expectations_json,
                local_corrections_json = excluded.local_corrections_json,
                continuity_notes_json = excluded.continuity_notes_json,
                updated_at = excluded.updated_at
            """,
            (
                profile_id,
                record.relationship_id,
                record.elephant_id,
                record.user_card_id,
                _json_list_text(record.interaction_preferences),
                _json_list_text(record.repair_history),
                _json_list_text(record.trust_markers),
                _json_list_text(record.expectations),
                _json_list_text(record.local_corrections),
                _json_list_text(record.continuity_notes),
                created_at,
                updated,
            ),
        )
        connection.commit()


def load_relationship_memory_for_profile(self, profile_id: str) -> RelationshipMemoryRecord | None:
    canonical_id = canonical_personal_model_id(profile_id)
    with self.connection() as connection:
        row = connection.execute(
            "SELECT * FROM canonical_relationship_memories WHERE profile_id = ?",
            (canonical_id,),
        ).fetchone()
    if row is None:
        return None
    return RelationshipMemoryRecord(
        relationship_id=row["relationship_id"],
        profile_id=row["profile_id"],
        elephant_id=row["elephant_id"],
        user_card_id=row["user_card_id"],
        interaction_preferences=_parse_json_list(row["interaction_preferences_json"]),
        repair_history=_parse_json_list(row["repair_history_json"]),
        trust_markers=_parse_json_list(row["trust_markers_json"]),
        expectations=_parse_json_list(row["expectations_json"]),
        local_corrections=_parse_json_list(row["local_corrections_json"]),
        continuity_notes=_parse_json_list(row["continuity_notes_json"]),
        created_at=_parse_datetime(row["created_at"]),
        updated_at=_parse_datetime(row["updated_at"]),
    )
