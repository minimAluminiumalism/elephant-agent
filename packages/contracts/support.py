"""Semantic-index contract shapes."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Mapping


_ALLOWED_OWNER_SCOPES = frozenset({"state", "personal_model", "episode", "skill"})


def _ensure_non_empty_text(value: str, *, name: str) -> None:
    if not str(value).strip():
        raise ValueError(f"{name} must not be empty")


def _ensure_owner_scope(value: str) -> None:
    if value not in _ALLOWED_OWNER_SCOPES:
        raise ValueError(f"owner_scope must be one of {sorted(_ALLOWED_OWNER_SCOPES)}: {value}")


@dataclass(frozen=True, slots=True)
class SemanticIndexEntry:
    semantic_index_entry_id: str
    owner_scope: str
    source_id: str
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
        _ensure_non_empty_text(self.source_id, name="semantic index source id")
        _ensure_non_empty_text(self.provider_id, name="semantic index provider id")
        _ensure_non_empty_text(self.model_id, name="semantic index model id")
        if self.dimensions <= 0:
            raise ValueError("semantic index dimensions must be positive")
        _ensure_non_empty_text(self.content_hash, name="semantic index content hash")
        _ensure_non_empty_text(self.backend, name="semantic index backend")
