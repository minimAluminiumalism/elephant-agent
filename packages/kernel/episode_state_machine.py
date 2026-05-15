"""Unified Episode state machine — single close path with guaranteed side-effects."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone

from packages.contracts.layers import Episode

from .runtime_support import KernelStoragePort


def close_episode(
    storage: KernelStoragePort,
    episode_id: str,
    *,
    reason: str,
    summary: str,
    current: datetime | None = None,
    semantic_summary_indexer: object | None = None,
) -> Episode:
    """Close an episode with guaranteed side-effects (indexing + learning enqueue).

    This is the ONLY path through which an episode should be closed.
    All close entry points (kernel single_turn, shell EOF, /clear, gateway idle)
    must call this function.

    Args:
        storage: The kernel storage port.
        episode_id: The episode to close.
        reason: Close reason — "final_response", "idle_timeout", "shell_exit",
                "shell_clear", "user_requested".
        summary: Exit summary text for future recall.
        current: Timestamp (defaults to now).
        semantic_summary_indexer: Optional semantic indexer for exit summary recall.

    Returns:
        The closed Episode.
    """
    if current is None:
        current = datetime.now(timezone.utc)

    episode = storage.load_episode(episode_id)
    if episode is None:
        raise KeyError(f"episode not found: {episode_id}")
    if episode.status == "closed":
        return episode  # idempotent

    closed = replace(
        episode,
        status="closed",
        ended_at=current,
        updated_at=current,
        exit_summary=summary or episode.exit_summary,
        metadata={**dict(episode.metadata), "closed_reason": reason},
    )
    storage.upsert_episode(closed)

    # Side-effect 1: Index exit summary for future semantic recall
    if semantic_summary_indexer is not None:
        index_exit = getattr(semantic_summary_indexer, "index_episode_exit", None)
        if callable(index_exit):
            try:
                index_exit(closed)
            except Exception:
                pass

    # Side-effect 2: Enqueue learning job
    enqueue = getattr(storage, "enqueue_learning_job", None)
    if callable(enqueue):
        loops = storage.list_loops(episode_id=episode_id)
        loop = loops[-1] if loops else None
        try:
            enqueue(
                job_type="episode_boundary_learning",
                trigger=_trigger_from_reason(reason),
                personal_model_id=closed.personal_model_id,
                state_id=closed.state_id,
                episode_id=closed.episode_id,
                loop_id=loop.loop_id if loop is not None else None,
                summary=closed.exit_summary,
                metadata={"closed_reason": reason, "source": "episode_state_machine"},
            )
        except Exception:
            pass

    return closed


def _trigger_from_reason(reason: str) -> str:
    """Map close reason to learning trigger type."""
    mapping = {
        "shell_exit": "episode_close",
        "shell_clear": "episode_close",
        "final_response": "episode_close",
        "user_requested": "episode_close",
    }
    return mapping.get(reason, "episode_close")
