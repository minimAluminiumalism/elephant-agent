"""Shared projection compaction value types."""

from __future__ import annotations

from dataclasses import dataclass

from packages.contracts.runtime import PromptMessage


@dataclass(frozen=True, slots=True)
class ContextProjectionCompactionResult:
    compacted: bool
    reason: str
    before_tokens: int
    after_tokens: int
    before_line_count: int
    after_line_count: int
    summary: str = ""
    protected_head_count: int = 0
    protected_tail_count: int = 0
    protected_ranges: tuple[str, ...] = ()
    compacted_line_count: int = 0
    selected_raw_ids: tuple[str, ...] = ()
    compaction_query: str = ""
    summary_hash: str = ""
    semantic_anchor_selected_count: int = 0
    semantic_anchor_cached_count: int = 0
    semantic_anchor_pending_count: int = 0
    missed_projection_embedding_count: int = 0
    semantic_anchor_wait_ms: int = 0
    # Cache-first retrieval status for the projection query vector. See
    # RecallReasons.vector_cache_status for the full vocabulary.
    vector_cache_status: str = ""

    def describe(self) -> str:
        status = "compacted" if self.compacted else "unchanged"
        parts = [
            f"{status} reason={self.reason}",
            f"tokens={self.before_tokens}->{self.after_tokens}",
            f"messages={self.before_line_count}->{self.after_line_count}",
            f"semantic_anchors={self.semantic_anchor_selected_count}",
            f"selected_raw={len(self.selected_raw_ids)}",
            f"cached={self.semantic_anchor_cached_count}",
            f"pending={self.semantic_anchor_pending_count}",
            f"missed={self.missed_projection_embedding_count}",
        ]
        if self.protected_ranges:
            parts.append(f"protected_ranges={'|'.join(self.protected_ranges)}")
        if self.summary_hash:
            parts.append(f"summary_hash={self.summary_hash}")
        return " ".join(parts)


@dataclass(frozen=True, slots=True)
class SessionMessageProjection:
    summary: str
    messages: tuple[PromptMessage, ...]
    result: ContextProjectionCompactionResult


@dataclass(frozen=True, slots=True)
class ProjectionSemanticAnchorStats:
    candidate_count: int = 0
    selected_group_count: int = 0
    cached_group_count: int = 0
    pending_group_count: int = 0
    missed_group_count: int = 0
    query_cached: bool = False
    query_pending: bool = False
    wait_ms: int = 0
    # See RecallReasons.vector_cache_status for the full vocabulary. Empty string
    # means the scorer was not invoked or embeddings were disabled upstream.
    vector_cache_status: str = ""


@dataclass(frozen=True, slots=True)
class ProjectionCompactionPolicy:
    trigger_ratio: float = 0.60
    target_ratio: float = 0.14
    protected_head_lines: int = 2
    protected_tail_lines: int = 10
    protected_tail_token_ratio: float = 0.20
    im_protected_head_lines: int = 0
    im_tail_window_seconds: int = 3600
    im_idle_gap_seconds: int = 1800
    minimum_trigger_tokens: int = 512
    minimum_target_tokens: int = 256
    minimum_tail_tokens: int = 256
    semantic_anchor_max_messages: int = 4
    max_summary_lines: int = 14

    def trigger_tokens(self, total_tokens: int) -> int:
        return max(self.minimum_trigger_tokens, int(max(0, total_tokens) * self.trigger_ratio))

    def target_tokens(self, total_tokens: int) -> int:
        trigger = self.trigger_tokens(total_tokens)
        target = max(self.minimum_target_tokens, int(max(0, total_tokens) * self.target_ratio))
        return min(trigger, target)

    def tail_tokens(self, total_tokens: int, *, force: bool = False) -> int:
        trigger = self.trigger_tokens(total_tokens)
        ratio = max(0.05, min(0.80, self.protected_tail_token_ratio))
        budget = max(self.minimum_tail_tokens, int(trigger * ratio))
        return max(1, budget // 2) if force else budget
