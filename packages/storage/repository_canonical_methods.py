"""Repository methods for first-class canonical Personal Model state."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from typing import Sequence

from packages.contracts import ElephantIdentityRecord

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
