"""Provider configuration contract shapes."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Mapping


def _ensure_non_empty_text(value: str, *, name: str) -> None:
    if not str(value).strip():
        raise ValueError(f"{name} must not be empty")


def _ensure_non_negative_int(value: int, *, name: str) -> None:
    if value < 0:
        raise ValueError(f"{name} must be non-negative")


@dataclass(frozen=True, slots=True)
class GenerationProviderConfig:
    generation_provider_config_id: str
    provider_id: str
    model_id: str
    provider_kind: str = "openai-compatible"
    base_url: str = ""
    api_key_secret_ref: str = ""
    reasoning_effort: str = ""
    context_window_tokens: int = 0
    status: str = "active"
    created_at: datetime | None = None
    updated_at: datetime | None = None
    metadata: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _ensure_non_empty_text(
            self.generation_provider_config_id,
            name="generation provider config id",
        )
        _ensure_non_empty_text(self.provider_id, name="generation provider id")
        _ensure_non_empty_text(self.model_id, name="generation provider model id")
        _ensure_non_empty_text(self.provider_kind, name="generation provider kind")
        _ensure_non_negative_int(
            self.context_window_tokens,
            name="generation provider context window tokens",
        )
        _ensure_non_empty_text(self.status, name="generation provider status")


@dataclass(frozen=True, slots=True)
class ActiveProviderSelection:
    active_provider_selection_id: str
    generation_provider_config_id: str
    embedding_provider_profile_id: str
    status: str = "active"
    selected_at: datetime | None = None
    metadata: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _ensure_non_empty_text(
            self.active_provider_selection_id,
            name="active provider selection id",
        )
        _ensure_non_empty_text(
            self.generation_provider_config_id,
            name="active generation provider config id",
        )
        _ensure_non_empty_text(
            self.embedding_provider_profile_id,
            name="active embedding provider profile id",
        )
        _ensure_non_empty_text(self.status, name="active provider selection status")
