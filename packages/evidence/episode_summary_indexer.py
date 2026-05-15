"""Auto-index committed content into the semantic index for recall.

## The gap this closes

Without a producer hook, the `semantic_index` package is inert — nothing
ever calls `index_document()`, so `memory.recall` can only fall back to
substring scans. We fix that by writing committed content (personal-model
records, episode exit summaries, state insights) into the index right after
they are persisted, so the *next* turn's recall has a populated search
surface.

## Usage

    indexer = SemanticSummaryIndexer(
        semantic_index=SemanticIndexService(...),
        embedding_service=DefaultEmbeddingService(...),
    )
    indexer.index_episode_exit(episode)
    indexer.index_personal_model_record(record)

Every call is best-effort: a missing service, an embedding failure, or a
backend outage returns ``None`` without raising. The producer path must
never block a governance write because indexing had a bad day.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from packages.contracts import Episode, Fact, Record, Step


__all__ = [
    "SemanticSummaryIndexer",
    "build_episode_summary_text",
    "build_personal_model_record_text",
    "build_personal_model_claim_text",
    "build_step_recall_text",
]


_MAX_TEXT_CHARS = 4_000
_NOISY_STEP_ACTIONS = frozenset(
    {
        "assemble_context",
        "call_model",
        "call_tool",
        "compact_context",
        "context_prompt",
        "effective_user_query",
        "model",
        "reflect",
        "write_memory",
    }
)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _truncate(text: str, limit: int = _MAX_TEXT_CHARS) -> str:
    collapsed = " ".join(str(text or "").split()).strip()
    if len(collapsed) <= limit:
        return collapsed
    return collapsed[: max(0, limit - 3)].rstrip(" ,;|") + "..."


def _is_startup_surface(value: object) -> bool:
    surface = str(value or "").strip().lower()
    return surface.startswith("cli.startup") or surface.endswith(".startup")


def _is_filtered_step(action: str, metadata: Mapping[str, object], *, text: str) -> bool:
    normalized_action = action.strip().lower()
    if normalized_action in _NOISY_STEP_ACTIONS:
        return True
    if str(metadata.get("tool_name") or "").strip():
        return True
    del text
    if str(metadata.get("event_type") or "").strip().lower() == "turn.internal":
        return True
    if _is_startup_surface(metadata.get("source")):
        return True
    return False


def build_episode_summary_text(episode: Episode) -> str:
    """Flatten an `Episode` into an indexable snippet for `semantic_index`.

    Combines exit_summary + entry_surface + metadata notes so a later recall
    query can match on any of them. No record ids in the indexed text — we
    want the semantic index to return content, not ids.
    """
    parts: list[str] = []
    exit_summary = str(getattr(episode, "exit_summary", "") or "").strip()
    entry_surface = str(getattr(episode, "entry_surface", "") or "").strip()
    if exit_summary:
        parts.append(f"exit: {exit_summary}")
    if entry_surface:
        parts.append(f"entry: {entry_surface}")
    metadata = dict(getattr(episode, "metadata", {}) or {})
    for key in ("topic", "focus", "note"):
        value = str(metadata.get(key) or "").strip()
        if value:
            parts.append(f"{key}: {value}")
    return _truncate(" | ".join(parts))


def build_personal_model_record_text(record: Record) -> str:
    """Flatten a personal-model record's title/summary/content for indexing."""
    payload = dict(record.payload or {})
    metadata = dict(record.metadata or {})
    pieces: list[str] = []
    for key in ("title", "summary", "content", "reason"):
        value = str(payload.get(key) or metadata.get(key) or "").strip()
        if value:
            pieces.append(value)
    return _truncate(" | ".join(pieces))


def build_personal_model_claim_text(fact: Fact) -> str:
    """Flatten one active Personal Model claim for semantic recall."""
    metadata = dict(fact.metadata or {})
    pieces = [
        f"lens: {fact.lens}",
        f"topic: {metadata.get('topic', '')}",
        f"claim: {fact.text}",
    ]
    return _truncate(" | ".join(piece for piece in pieces if piece.strip()))


def build_step_recall_text(step: Step) -> str:
    """Flatten a kernel Step into an indexable historical recall document."""
    metadata = dict(step.metadata or {})
    action = str(step.action or "").strip()
    normalized_action = action.lower()
    if normalized_action == "record_input":
        parts = [str(metadata.get("user_query") or metadata.get("raw_user_query") or "").strip()]
    elif normalized_action == "emit_response":
        parts = [str(metadata.get("final_response") or metadata.get("assistant_response") or step.summary).strip()]
    elif normalized_action == "reply":
        parts = [str(step.summary or "").strip(), str(metadata.get("final_response") or metadata.get("assistant_response") or "").strip()]
    else:
        parts = [
            str(step.summary or "").strip(),
            str(metadata.get("user_query") or metadata.get("raw_user_query") or "").strip(),
            str(metadata.get("final_response") or metadata.get("assistant_response") or "").strip(),
        ]
    text = _truncate(" | ".join(dict.fromkeys(part for part in parts if part)))
    if _is_filtered_step(action, metadata, text=text):
        return ""
    return text


@dataclass(frozen=True, slots=True)
class SemanticSummaryIndexer:
    """Best-effort bridge from committed content → semantic_index.

    `semantic_index`: SemanticIndexService | None — when None, all methods no-op.
    `embedding_service`: an object exposing `embed_text(text, *, request_id, ...)
                        -> EmbeddingVector` (matches `DefaultEmbeddingService`).
    `repository`: optional RuntimeStorageRepository. When provided and the
                  `source_record_id` does not already exist, the indexer
                  writes a stub Record first so the semantic_index_entries
                  FK is satisfied. Required for `index_episode_exit` because
                  Episode rows live in the `episodes` table, not `records`.
    """

    semantic_index: Any = None
    embedding_service: Any = None
    repository: Any = None
    provider_id: str = ""
    model_id: str = ""

    def _embed(self, text: str) -> tuple[Any | None, int]:
        service = self.embedding_service
        if service is None or not text.strip():
            return None, 0
        try:
            vec = service.embed_text(
                text,
                request_id=f"summary-index-{uuid4().hex}",
                task="index",
                latency_mode="balanced",
            )
        except Exception:
            return None, 0
        try:
            return vec.values, int(vec.dimensions)
        except AttributeError:
            return None, 0

    def _index(
        self,
        *,
        text: str,
        source_record_id: str,
        owner_scope: str,
        personal_model_id: str | None,
        state_id: str | None,
        metadata: Mapping[str, str] | None = None,
        ensure_record: bool = False,
        record_kind: str = "derived",
        record_schema_version: str = "",
        record_layer_type: str | None = None,
        record_created_at: datetime | None = None,
    ) -> object | None:
        service = self.semantic_index
        if service is None:
            return None
        if not source_record_id.strip() or not text.strip():
            return None
        vec_values, dimensions = self._embed(text)
        if vec_values is None or dimensions <= 0:
            return None
        try:
            from packages.semantic_index import SemanticIndexDocument
        except Exception:
            return None
        provider_id = self.provider_id or (
            getattr(self.embedding_service, "registry", None)
            and getattr(self.embedding_service.registry.default(), "provider_id", "")
            or ""
        )
        model_id = self.model_id or (
            getattr(self.embedding_service, "registry", None)
            and getattr(self.embedding_service.registry.default(), "model_id", "")
            or ""
        )
        if not provider_id or not model_id:
            return None
        if ensure_record and self.repository is not None:
            try:
                existing = self.repository.load_record(source_record_id)
            except Exception:
                existing = None
            if existing is None:
                pm_ref = personal_model_id if owner_scope == "personal_model" else None
                state_ref = state_id if owner_scope in {"state", "episode"} else None
                try:
                    stub = Record(
                        record_id=source_record_id,
                        kind=record_kind,
                        schema_version=record_schema_version or f"{owner_scope}_summary/v1",
                        owner_scope=owner_scope,
                        personal_model_id=pm_ref,
                        state_id=state_ref,
                        layer_type=record_layer_type,
                        payload={"text": text},
                        created_at=record_created_at or _utc_now(),
                        metadata={k: str(v) for k, v in dict(metadata or {}).items()},
                    )
                    self.repository.upsert_record(stub)
                except Exception:
                    return None
        try:
            document = SemanticIndexDocument(
                source_record_id=source_record_id,
                owner_scope=owner_scope,
                text=text,
                vector=tuple(vec_values),
                provider_id=provider_id,
                model_id=model_id,
                dimensions=dimensions,
                personal_model_id=personal_model_id,
                state_id=state_id,
                metadata={k: str(v) for k, v in dict(metadata or {}).items()},
            )
        except Exception:
            return None
        try:
            return service.index_document(document)
        except Exception:
            return None

    def index_episode_exit(self, episode: Episode) -> object | None:
        """Index an Episode's exit_summary for cross-episode recall."""
        if episode is None:
            return None
        text = build_episode_summary_text(episode)
        if not text:
            return None
        personal_model_id = str(getattr(episode, "personal_model_id", "") or "").strip() or None
        state_id = str(getattr(episode, "state_id", "") or "").strip() or None
        return self._index(
            text=text,
            source_record_id=f"episode:{episode.episode_id}",
            owner_scope="state",
            personal_model_id=personal_model_id,
            state_id=state_id,
            metadata={
                "kind": "episode_summary",
                "episode_id": episode.episode_id,
                "status": str(getattr(episode, "status", "") or ""),
                "memory_lifecycle": "episode",
            },
            ensure_record=True,
            record_kind="derived",
            record_schema_version="episode_summary/v1",
            record_layer_type="episode_summary",
            record_created_at=getattr(episode, "ended_at", None) or getattr(episode, "started_at", None),
        )

    def index_step(self, step: Step) -> object | None:
        """Index one kernel Step as historical recall material."""
        if step is None:
            return None
        text = build_step_recall_text(step)
        if not text:
            return None
        metadata = dict(step.metadata or {})
        return self._index(
            text=text,
            source_record_id=f"record:{step.step_id}",
            owner_scope="state",
            personal_model_id=step.personal_model_id,
            state_id=step.state_id,
            metadata={
                "kind": "step",
                "step_id": step.step_id,
                "loop_id": step.loop_id,
                "episode_id": step.episode_id,
                "action": step.action,
                "phase": step.phase,
                "status": step.status,
                "memory_lifecycle": "episode",
            },
            ensure_record=True,
            record_kind="derived",
            record_schema_version="step/v1",
            record_layer_type="step",
            record_created_at=step.created_at,
        )

    def index_personal_model_record(self, record: Record) -> object | None:
        """Index a committed Personal Model record for future recall."""
        if record is None:
            return None
        text = build_personal_model_record_text(record)
        if not text:
            return None
        personal_model_id = str(getattr(record, "personal_model_id", "") or "").strip() or None
        state_id = str(getattr(record, "state_id", "") or "").strip() or None
        metadata = dict(getattr(record, "metadata", {}) or {})
        return self._index(
            text=text,
            source_record_id=record.record_id,
            owner_scope="personal_model",
            personal_model_id=personal_model_id,
            state_id=state_id,
            metadata={
                "kind": "personal_model_record",
                "record_id": record.record_id,
                "layer_type": str(getattr(record, "layer_type", "") or ""),
                "memory_lifecycle": "preference",
            },
        )

    def index_personal_model_claim(self, fact: Fact) -> object | None:
        """Index one active Personal Model claim for future recall."""
        if fact is None or fact.status != "active":
            return None
        text = build_personal_model_claim_text(fact)
        if not text:
            return None
        metadata = dict(fact.metadata or {})
        return self._index(
            text=text,
            source_record_id=fact.fact_id,
            owner_scope="personal_model",
            personal_model_id=fact.personal_model_id,
            state_id=None,
            metadata={
                "kind": "personal_model_claim",
                "claim_ref": fact.fact_id,
                "lens": fact.lens,
                "topic": str(metadata.get("topic") or ""),
                "text": fact.text,
                "reason": str(metadata.get("reason") or ""),
                "confidence": str(fact.confidence),
                "memory_lifecycle": "preference",
            },
            ensure_record=True,
            record_kind="derived",
            record_schema_version="personal_model_claim/v1",
            record_layer_type="personal_model_claim",
        )
