"""Unified context compression pipeline for CLI and Gateway.

Single entry point for both systems:
- LLM-based compress via reflect agent (high quality, requires sub-agent capability)
- Deterministic fallback (truncate + template summary, for hot-path overflow retries)

Split logic protects the most recent tail while compressing older or oversized
completed context into a reference summary.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any, Callable, Protocol

from packages.contracts.runtime import PromptMessage

from .session_projection import (
    SessionContextEpoch,
    compact_session_context_epoch,
    estimate_epoch_prompt_tokens,
)


@dataclass(frozen=True, slots=True)
class CompressResult:
    """Outcome of a compress operation."""

    compressed: bool
    summary: str
    before_messages: int
    after_messages: int
    before_tokens: int
    after_tokens: int
    method: str  # "reflect", "deterministic", "skipped"


class ReflectCompressor(Protocol):
    """Protocol for LLM-based compression via reflect agent."""

    def __call__(
        self,
        to_summarize: tuple[PromptMessage, ...],
        tail: tuple[PromptMessage, ...],
        *,
        session_id: str,
        context_limit: int,
    ) -> str:
        """Run reflect compress agent, return summary text."""
        ...


def compress_epoch(
    epoch: SessionContextEpoch,
    *,
    context_limit: int,
    usage_tokens: int,
    trigger_ratio: float = 0.85,
    reflect_compressor: ReflectCompressor | None = None,
    session_id: str = "",
) -> tuple[SessionContextEpoch, CompressResult] | None:
    """Unified compress entry point for both CLI and Gateway.

    Returns None if compression is not needed or not possible.
    Returns (updated_epoch, result) on successful compression.

    - reflect_compressor: LLM-based compress (pass None for hot-path deterministic fallback)
    - trigger_ratio: fraction of context_limit that triggers compression
    """
    if usage_tokens <= 0 or context_limit <= 0:
        return None
    trigger_tokens = max(1, int(context_limit * trigger_ratio))
    if usage_tokens < trigger_tokens:
        return None
    if not epoch.frozen or not epoch.history_messages:
        return None

    history = epoch.history_messages
    to_summarize, tail = split_for_compress(history)
    if not to_summarize:
        return None

    resolved_session_id = session_id or epoch.session_id

    # Try LLM-based compress first
    summary = ""
    method = "deterministic"
    if reflect_compressor is not None:
        try:
            summary = reflect_compressor(
                to_summarize, tail,
                session_id=resolved_session_id,
                context_limit=context_limit,
            )
            if summary.strip():
                method = "reflect"
        except Exception:
            summary = ""

    # Deterministic fallback
    if not summary.strip():
        summary = _deterministic_summary(to_summarize, history_count=len(history))
        method = "deterministic"

    # Apply compression: replace history with tail, set summary
    before_tokens = estimate_epoch_prompt_tokens(
        epoch, history_messages=history, compacted_summary=epoch.compacted_history_summary,
    )
    updated, _result = compact_session_context_epoch(
        epoch,
        total_tokens=context_limit,
        reason="usage",
        force=True,
        summary_text=summary,
        tail_messages=tail,
    )

    # Update Episode resume in frozen_prefix
    from packages.kernel.generation_context import (
        _strip_prompt_sections,
        _append_prompt_section,
    )
    updated_prefix = _strip_prompt_sections(updated.frozen_prefix, "Episode resume")
    updated_prefix = _append_prompt_section(
        updated_prefix,
        "Episode resume",
        (f"Reference summary: {summary}",),
    )
    updated = replace(updated, frozen_prefix=updated_prefix)

    after_tokens = estimate_epoch_prompt_tokens(
        updated, history_messages=tail, compacted_summary=summary,
    )

    result = CompressResult(
        compressed=True,
        summary=summary,
        before_messages=len(history),
        after_messages=len(tail),
        before_tokens=before_tokens,
        after_tokens=after_tokens,
        method=method,
    )
    return updated, result


def split_for_compress(
    messages: tuple[PromptMessage, ...],
    *,
    protected_tail_turns: int = 2,
) -> tuple[tuple[PromptMessage, ...], tuple[PromptMessage, ...]]:
    """Split messages into (to_summarize, protected_tail).

    For multi-turn conversations: keeps last N user turns intact.
    For single long turns (1 user + many tools): keeps the first user query plus
    the last ~25% of messages (final assistant response + recent tool context).
    For very short high-usage histories (for example one huge user request plus
    one assistant reply), keeps only the latest completed tail message and
    summarizes the earlier oversized context. Callers only invoke this splitter
    after a high-usage threshold, so this branch does not affect ordinary short
    conversations.
    """
    total = len(messages)
    if total < 2:
        return (), messages
    if total < 4:
        return messages[:-1], messages[-1:]

    # Find user-message boundaries
    user_starts: list[int] = []
    for i, msg in enumerate(messages):
        if msg.role == "user" and msg.content.strip():
            user_starts.append(i)

    # Normal multi-turn case: 3+ user turns → keep last 2 intact
    if len(user_starts) > protected_tail_turns:
        tail_start = user_starts[-protected_tail_turns]
        # Ensure we're actually compressing a meaningful amount (>30%)
        if tail_start > total * 0.3:
            return messages[:tail_start], messages[tail_start:]

    # Few turns OR the normal split didn't compress enough:
    # Use aggressive compression — keep first user + last N messages
    # This handles "1 user query → 100 tool calls → assistant response"
    keep_tail_count = max(6, min(total // 3, 20))  # Keep 1/3 but max 20 messages
    tail_start_idx = max(1, total - keep_tail_count)

    # Always include the first user message
    tail_indices: set[int] = {0}
    # Keep the last N messages
    for i in range(tail_start_idx, total):
        tail_indices.add(i)
    # Also keep any user/assistant content messages (they're rare and valuable)
    for i in range(1, tail_start_idx):
        msg = messages[i]
        if msg.role == "user" and msg.content.strip():
            tail_indices.add(i)
        elif msg.role == "assistant" and msg.content.strip() and not msg.tool_calls:
            tail_indices.add(i)

    tail = tuple(messages[i] for i in sorted(tail_indices))
    to_summarize = tuple(messages[i] for i in range(total) if i not in tail_indices)
    if to_summarize:
        return to_summarize, tail

    # Ultimate fallback: compress first 60%
    if total >= 4:
        cut = max(1, int(total * 0.6))
        return messages[:cut], messages[cut:]

    return (), messages


def _deterministic_summary(
    to_summarize: tuple[PromptMessage, ...],
    *,
    history_count: int,
) -> str:
    """Generate a simple heuristic summary when LLM compress is unavailable."""
    user_messages = [msg for msg in to_summarize if msg.role == "user" and msg.content.strip()]
    tool_count = sum(1 for msg in to_summarize if msg.role == "tool")

    parts: list[str] = []
    parts.append(f"[Context compressed] {len(to_summarize)} of {history_count} messages summarized.")

    if user_messages:
        # Include abbreviated user queries for continuity
        for msg in user_messages[:3]:
            text = msg.content.strip()[:120]
            parts.append(f"User asked: {text}")

    if tool_count > 0:
        parts.append(f"({tool_count} tool interactions were executed.)")

    return " ".join(parts)
