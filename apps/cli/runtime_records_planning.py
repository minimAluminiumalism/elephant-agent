"""Evidence-retrieval planner used by wake / resume surfaces.

Extracted from runtime_records.py so that file stays under the
1000-line lint budget. This module owns two thin helpers the CLI
runtime calls when building the resume packet for a wake session:

- ``plan_memory_recovery`` runs one evidence-retrieval probe with a
  relationship-aware query, falls back to raw scope-scoped memory
  listing when the probe returns nothing, and returns a full
  ``_PlanningMemoryRecovery`` record including the resume packet.
- ``plan_memories`` unwraps the tuple of ``MemoryRecord`` from the
  recovery record (used when the caller only needs the candidates).
"""

from __future__ import annotations

from typing import Any

from packages.contracts.layers import Episode
from packages.contracts.runtime import EvidenceRetrievalRequest, MemoryRecord

from .runtime_cognition import (
    _list_scope_memories,
    _memory_query_with_relationship,
    _memory_scope_reason,
    _memory_scope_session_ids,
)
from .runtime_support import _PlanningMemoryRecovery


def plan_memory_recovery(
    runtime: Any,
    session: Episode,
    *,
    limit: int = 8,
) -> _PlanningMemoryRecovery:
    relationship = runtime.inspect_relationship(profile_id=session.personal_model_id)
    query = _memory_query_with_relationship(runtime.repository, relationship=relationship)
    work_item_ids: tuple[str, ...] = ()
    scope_session_ids = _memory_scope_session_ids(runtime.repository, session)
    scope_reason = _memory_scope_reason(
        session=session,
        relationship=relationship,
        scope_session_ids=scope_session_ids,
    )
    request = EvidenceRetrievalRequest(
        episode_id=session.episode_id,
        personal_model_id=session.personal_model_id,
        elephant_id=session.elephant_id,
        lineage_episode_ids=scope_session_ids,
        work_item_ids=work_item_ids,
        query=query,
        scopes=("episode", "lineage", "elephant") if session.elephant_id else ("episode", "lineage"),
        latency_mode="fast",
        limit=limit,
        scope_reason=scope_reason,
        relationship_hints=relationship.continuity_notes,
    )
    retrieval = runtime.memory_runtime.retrieve_evidence(request)
    artifact_ids: tuple[str, ...] = ()
    constraint_ids: tuple[str, ...] = ()
    resume_packet = runtime.memory_runtime.build_resume_packet(
        request,
        retrieval,
        next_move="wake-next-step",
        artifact_ids=artifact_ids,
        constraint_ids=constraint_ids,
    )
    memories = tuple(candidate.memory for candidate in retrieval.candidates)
    if memories:
        return _PlanningMemoryRecovery(
            memories=memories,
            query=query,
            work_item_ids=work_item_ids,
            scope_episode_ids=retrieval.scope_episode_ids,
            scope_reason=retrieval.scope_reason,
            retrieval=retrieval,
            resume_packet=resume_packet,
        )
    listed = _list_scope_memories(runtime.repository, scope_session_ids=scope_session_ids)
    fallback = listed[-limit:] if listed else ()
    return _PlanningMemoryRecovery(
        memories=fallback,
        query=query,
        work_item_ids=work_item_ids,
        scope_episode_ids=scope_session_ids,
        scope_reason=scope_reason,
        retrieval=retrieval,
        resume_packet=resume_packet,
    )


def plan_memories(
    runtime: Any,
    session: Episode,
    *,
    limit: int = 8,
) -> tuple[MemoryRecord, ...]:
    return plan_memory_recovery(runtime, session, limit=limit).memories


__all__ = ["plan_memory_recovery", "plan_memories"]
