"""Evidence-retrieval planner used by wake / resume surfaces.

Extracted from runtime_records.py so that file stays under the
1000-line lint budget. This module owns two thin helpers the CLI
runtime calls when building the resume packet for a wake session:

- ``plan_recall_evidence_recovery`` runs one evidence-retrieval probe with a
  relationship-aware query, falls back to raw scope-scoped evidence
  listing when the probe returns nothing, and returns a full
  ``_PlanningRecallRecovery`` record including the resume packet.
- ``plan_recall_evidence`` unwraps the tuple of ``RecallEvidence`` from the
  recovery record (used when the caller only needs the candidates).
"""

from __future__ import annotations

from typing import Any

from packages.contracts.layers import Episode
from packages.contracts.runtime import EvidenceRetrievalRequest, RecallEvidence

from .runtime_cognition import (
    _list_scope_recall_evidence,
    _recall_query_with_relationship,
    _recall_scope_reason,
    _recall_scope_session_ids,
)
from .runtime_support import _PlanningRecallRecovery


def plan_recall_evidence_recovery(
    runtime: Any,
    session: Episode,
    *,
    limit: int = 8,
) -> _PlanningRecallRecovery:
    relationship = runtime.inspect_relationship(profile_id=session.personal_model_id)
    query = _recall_query_with_relationship(runtime.repository, relationship=relationship)
    work_item_ids: tuple[str, ...] = ()
    scope_session_ids = _recall_scope_session_ids(runtime.repository, session)
    scope_reason = _recall_scope_reason(
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
    retrieval = runtime.recall_runtime.retrieve_evidence(request)
    artifact_ids: tuple[str, ...] = ()
    constraint_ids: tuple[str, ...] = ()
    resume_packet = runtime.recall_runtime.build_resume_packet(
        request,
        retrieval,
        next_move="wake-next-step",
        artifact_ids=artifact_ids,
        constraint_ids=constraint_ids,
    )
    recall_items = tuple(candidate.evidence for candidate in retrieval.candidates)
    if recall_items:
        return _PlanningRecallRecovery(
            recall_items=recall_items,
            query=query,
            work_item_ids=work_item_ids,
            scope_episode_ids=retrieval.scope_episode_ids,
            scope_reason=retrieval.scope_reason,
            retrieval=retrieval,
            resume_packet=resume_packet,
        )
    listed = _list_scope_recall_evidence(runtime.repository, scope_session_ids=scope_session_ids)
    fallback = listed[-limit:] if listed else ()
    return _PlanningRecallRecovery(
        recall_items=fallback,
        query=query,
        work_item_ids=work_item_ids,
        scope_episode_ids=scope_session_ids,
        scope_reason=scope_reason,
        retrieval=retrieval,
        resume_packet=resume_packet,
    )


def plan_recall_evidence(
    runtime: Any,
    session: Episode,
    *,
    limit: int = 8,
) -> tuple[RecallEvidence, ...]:
    return plan_recall_evidence_recovery(runtime, session, limit=limit).recall_items


__all__ = ["plan_recall_evidence_recovery", "plan_recall_evidence"]
