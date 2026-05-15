"""Scoped explicit memory-capture contracts and helpers."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from typing import Mapping

from packages.contracts import Grounding, MemoryEntry, Record

_CAPTURE_SCOPES = frozenset({"state", "personal_model"})
_STATE_CAPTURE_KINDS = frozenset({"knowledge", "procedural"})
_PERSONAL_MODEL_CAPTURE_KINDS = frozenset({"core", "style", "knowledge", "procedural", "relationship"})
_CAPTURE_SENSITIVITIES = frozenset({"low", "medium", "high"})


def _ensure_capture_scope(value: str) -> None:
    if value not in _CAPTURE_SCOPES:
        raise ValueError(f"memory capture scope must be one of {sorted(_CAPTURE_SCOPES)}: {value}")


def _ensure_capture_sensitivity(value: str) -> None:
    if value not in _CAPTURE_SENSITIVITIES:
        raise ValueError(
            f"memory capture sensitivity must be one of {sorted(_CAPTURE_SENSITIVITIES)}: {value}"
        )


def _allowed_capture_kinds(scope: str) -> frozenset[str]:
    return _STATE_CAPTURE_KINDS if scope == "state" else _PERSONAL_MODEL_CAPTURE_KINDS


def _capture_record_layer_type(kind: str) -> str:
    return {
        "core": "core",
        "style": "style",
        "knowledge": "knowledge",
        "procedural": "procedural",
        "relationship": "relationship",
    }[kind]


def _capture_hash(*parts: str) -> str:
    normalized = "|".join(part.strip() for part in parts)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]


@dataclass(frozen=True, slots=True)
class MemoryCaptureRequest:
    scope: str
    kind: str
    content: str
    source_record_id: str
    user_directed: bool = True
    sensitivity: str = "low"
    personal_model_id: str | None = None
    state_id: str | None = None
    episode_id: str | None = None
    loop_id: str | None = None
    step_ids: tuple[str, ...] = ()
    tool_refs: tuple[str, ...] = ()
    model_refs: tuple[str, ...] = ()
    created_at: datetime | None = None
    metadata: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _ensure_capture_scope(self.scope)
        if self.kind not in _allowed_capture_kinds(self.scope):
            raise ValueError(
                f"memory capture kind must be one of {sorted(_allowed_capture_kinds(self.scope))} for {self.scope}: {self.kind}"
            )
        if not self.content.strip():
            raise ValueError("memory capture content must not be empty")
        if not self.source_record_id.strip():
            raise ValueError("memory capture source_record_id must not be empty")
        _ensure_capture_sensitivity(self.sensitivity)
        if len(set(self.step_ids)) != len(self.step_ids):
            raise ValueError("memory capture step_ids must be unique")


@dataclass(frozen=True, slots=True)
class MemoryCaptureResult:
    status: str
    scope: str
    kind: str
    reason: str
    grounding: Grounding | None = None
    canonical_record: Record | None = None
    memory_entry: MemoryEntry | None = None

    @property
    def committed(self) -> bool:
        return self.status == "committed"


__all__ = [name for name in globals() if not name.startswith("__")]
