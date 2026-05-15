"""Durable support-record contract shapes."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Mapping


_ALLOWED_RECORD_KINDS = frozenset({"layer", "artifact", "derived"})
_ALLOWED_OWNER_SCOPES = frozenset({"state", "personal_model", "episode", "skill"})


def _ensure_non_empty_text(value: str, *, name: str) -> None:
    if not str(value).strip():
        raise ValueError(f"{name} must not be empty")


def _ensure_unique_ids(values: tuple[str, ...], *, name: str) -> None:
    if len(set(values)) != len(values):
        raise ValueError(f"{name} ids must be unique")


def _ensure_confidence(value: float, *, name: str) -> None:
    if not 0.0 <= value <= 1.0:
        raise ValueError(f"{name} must stay between 0.0 and 1.0")


def _ensure_owner_scope(value: str) -> None:
    if value not in _ALLOWED_OWNER_SCOPES:
        raise ValueError(f"owner_scope must be one of {sorted(_ALLOWED_OWNER_SCOPES)}: {value}")


@dataclass(frozen=True, slots=True)
class Record:
    record_id: str
    kind: str
    schema_version: str
    payload: Mapping[str, object] = field(default_factory=dict)
    owner_scope: str | None = None
    personal_model_id: str | None = None
    state_id: str | None = None
    layer_type: str | None = None
    artifact_uri: str | None = None
    created_at: datetime | None = None
    metadata: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _ensure_non_empty_text(self.record_id, name="record id")
        if self.kind not in _ALLOWED_RECORD_KINDS:
            raise ValueError(f"record kind must be one of {sorted(_ALLOWED_RECORD_KINDS)}: {self.kind}")
        _ensure_non_empty_text(self.schema_version, name="record schema version")
        if self.owner_scope is not None:
            _ensure_owner_scope(self.owner_scope)


@dataclass(frozen=True, slots=True)
class Grounding:
    grounding_id: str
    source_record_ids: tuple[str, ...]
    summary: str = ""
    confidence: float = 0.0
    policy_decision: str = ""
    repair_state: str = ""
    created_at: datetime | None = None
    metadata: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _ensure_non_empty_text(self.grounding_id, name="grounding id")
        if not self.source_record_ids:
            raise ValueError("grounding source_record_ids must not be empty")
        _ensure_unique_ids(self.source_record_ids, name="grounding source record")
        _ensure_confidence(self.confidence, name="grounding confidence")


@dataclass(frozen=True, slots=True)
class MemoryEntry:
    memory_entry_id: str
    owner_scope: str
    kind: str
    content: str
    grounding_ids: tuple[str, ...]
    personal_model_id: str | None = None
    state_id: str | None = None
    sensitivity: str = ""
    status: str = "active"
    created_at: datetime | None = None
    updated_at: datetime | None = None
    metadata: Mapping[str, str] = field(default_factory=dict)
    # LLM-rated (or runtime-heuristic) significance score in [0.0, 1.0].
    # 0.5 is the backfill default — we don't pretend we know how important
    # a historic entry was. Frontier research (Generative Agents, Park et
    # al. 2023) uses importance as one RRF signal during recall and shows
    # ~2x precision lift over semantic-only ranking.
    importance: float = 0.5

    def __post_init__(self) -> None:
        _ensure_non_empty_text(self.memory_entry_id, name="memory entry id")
        _ensure_owner_scope(self.owner_scope)
        _ensure_non_empty_text(self.kind, name="memory entry kind")
        _ensure_non_empty_text(self.content, name="memory entry content")
        if not self.grounding_ids:
            raise ValueError("memory entry grounding_ids must not be empty")
        _ensure_unique_ids(self.grounding_ids, name="memory entry grounding")
        # Clamp so upstream bugs (e.g. LLM returning "0.95" but string-typed)
        # don't poison the index.
        if not (0.0 <= float(self.importance) <= 1.0):
            raise ValueError(
                f"memory entry importance must be in [0.0, 1.0]: {self.importance}"
            )


@dataclass(frozen=True, slots=True)
class ReflectionProposal:
    reflection_proposal_id: str
    owner_scope: str
    proposal_type: str
    content: str
    grounding_ids: tuple[str, ...]
    personal_model_id: str | None = None
    state_id: str | None = None
    target_id: str | None = None
    status: str = "pending"
    created_at: datetime | None = None
    updated_at: datetime | None = None
    metadata: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _ensure_non_empty_text(self.reflection_proposal_id, name="reflection proposal id")
        _ensure_owner_scope(self.owner_scope)
        _ensure_non_empty_text(self.proposal_type, name="reflection proposal type")
        _ensure_non_empty_text(self.content, name="reflection proposal content")
        if not self.grounding_ids:
            raise ValueError("reflection proposal grounding_ids must not be empty")
        _ensure_unique_ids(self.grounding_ids, name="reflection proposal grounding")


@dataclass(frozen=True, slots=True)
class SemanticIndexEntry:
    semantic_index_entry_id: str
    owner_scope: str
    source_record_id: str
    provider_id: str
    model_id: str
    dimensions: int
    content_hash: str
    personal_model_id: str | None = None
    state_id: str | None = None
    backend: str = "sqlite-vec"
    vector_ref: str = ""
    status: str = "indexed"
    created_at: datetime | None = None
    updated_at: datetime | None = None
    metadata: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _ensure_non_empty_text(self.semantic_index_entry_id, name="semantic index entry id")
        _ensure_owner_scope(self.owner_scope)
        _ensure_non_empty_text(self.source_record_id, name="semantic index source record id")
        _ensure_non_empty_text(self.provider_id, name="semantic index provider id")
        _ensure_non_empty_text(self.model_id, name="semantic index model id")
        if self.dimensions <= 0:
            raise ValueError("semantic index dimensions must be positive")
        _ensure_non_empty_text(self.content_hash, name="semantic index content hash")
        _ensure_non_empty_text(self.backend, name="semantic index backend")
