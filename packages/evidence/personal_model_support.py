"""PersonalModel component write helpers (v5 — Observation/Fact shape).

This module provides the write API used by the rest of the codebase
(`evidence.memory_runtime_impl`, `evidence.personal_model_fast_learn`,
`learning.personal_model_evolution`, etc.).

Under the v5 design (see ``docs/agent/plans/learning-shape.md``) we no longer
have six-component storage types (CoreMemory, PersonalityStyleModel,
PersonalKnowledge, EpisodicIndex, ProceduralMemory, RelationshipMemory).
Instead we have two tables: **Observation** (raw signals) and **Fact**
(durable prompt-visible statements). Big Five becomes one of several
sub-lens extraction lenses, not a storage shape.

This module keeps a ``PersonalModelWriteRequest`` shape so callers don't all
need to rewrite at once, but internally maps every write to either an
Observation or a Fact depending on the ``maturity_state`` / user_directed
/ user_confirmed inputs.

Mapping rules:

- ``user_directed=True`` or ``user_confirmed=True`` → write a **Fact**
  (status="active", source="user_explicit", confidence=1.0).
- All other writes → write an **Observation** with ``source`` derived from
  the request metadata (``pm_agent_extract`` by default).

Lens inference from the legacy ``kind`` argument:

    core          → trait (generic facts are trait-ish in the v5 taxonomy)
    style         → rapport
    knowledge     → knowledge
    procedural    → knowledge
    relationship  → rapport
    episodic_index→ knowledge
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Mapping

from packages.contracts import (
    Fact,
    Grounding,
    MemoryEntry,
    Observation,
    Record,
    ReflectionProposal,
)

from .memory_capture_support import _CAPTURE_SENSITIVITIES, _capture_hash
from .recall_lifecycle import infer_recall_lifecycle_metadata

_PERSONAL_MODEL_WRITE_KINDS = frozenset(
    {"core", "style", "knowledge", "procedural", "relationship", "episodic_index"}
)
# Legacy maturity states still accepted on input; mapped internally to v5.
_LEGACY_MATURITY_STATES = frozenset({"observed", "hypothesized", "committed"})

# Legacy kind → v5 lens
_LEGACY_KIND_TO_LENS: Mapping[str, str] = {
    "core": "trait",
    "style": "rapport",
    "knowledge": "knowledge",
    "procedural": "knowledge",
    "relationship": "rapport",
    "episodic_index": "knowledge",
}


def _ensure_text(value: str, *, name: str) -> None:
    if not value.strip():
        raise ValueError(f"{name} must not be empty")


def _ensure_unique(values: tuple[str, ...], *, name: str) -> None:
    if len(set(values)) != len(values):
        raise ValueError(f"{name} must be unique")


@dataclass(frozen=True, slots=True)
class StyleTraitSignalInput:
    """Kept for signature compatibility.  Trait / direction become an
    Observation with sub_lens="big_five.<trait>".
    """

    trait: str
    signal: str
    direction: str = ""
    observed_at: datetime | None = None
    metadata: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _ensure_text(self.trait, name="style trait signal trait")
        _ensure_text(self.signal, name="style trait signal")


@dataclass(frozen=True, slots=True)
class PersonalModelWriteRequest:
    kind: str
    content: str
    source_record_ids: tuple[str, ...]
    personal_model_id: str | None = None
    state_id: str | None = None
    maturity_state: str = "observed"
    confidence: float = 0.0
    sensitivity: str = "low"
    support_count: int = 1
    approval_state: str = "pending"
    conflict_state: str = "none"
    correction_state: str = "none"
    user_directed: bool = False
    user_confirmed: bool = False
    user_edited: bool = False
    component_kind: str = ""
    subject: str = ""
    title: str = ""
    summary: str = ""
    state_refs: tuple[str, ...] = ()
    episode_ids: tuple[str, ...] = ()
    turning_points: tuple[str, ...] = ()
    correction_refs: tuple[str, ...] = ()
    trigger_conditions: tuple[str, ...] = ()
    steps: tuple[str, ...] = ()
    related_skill_ids: tuple[str, ...] = ()
    communication_preferences: tuple[str, ...] = ()
    autonomy_boundaries: tuple[str, ...] = ()
    trait_signals: tuple[StyleTraitSignalInput, ...] = ()
    metadata: Mapping[str, str] = field(default_factory=dict)
    created_at: datetime | None = None

    def __post_init__(self) -> None:
        if self.kind not in _PERSONAL_MODEL_WRITE_KINDS:
            raise ValueError(
                f"personal model write kind must be one of {sorted(_PERSONAL_MODEL_WRITE_KINDS)}: {self.kind}"
            )
        _ensure_text(self.content, name="personal model write content")
        if not self.source_record_ids:
            raise ValueError("personal model write source_record_ids must not be empty")
        _ensure_unique(self.source_record_ids, name="personal model write source_record_ids")
        if self.maturity_state not in _LEGACY_MATURITY_STATES:
            raise ValueError(
                f"personal model write maturity_state must be one of {sorted(_LEGACY_MATURITY_STATES)}: {self.maturity_state}"
            )
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("personal model write confidence must stay between 0.0 and 1.0")
        if self.sensitivity not in _CAPTURE_SENSITIVITIES:
            raise ValueError(
                f"personal model write sensitivity must be one of {sorted(_CAPTURE_SENSITIVITIES)}: {self.sensitivity}"
            )
        if self.support_count < 1:
            raise ValueError("personal model write support_count must be at least 1")
        _ensure_unique(self.state_refs, name="personal model write state_refs")
        _ensure_unique(self.episode_ids, name="personal model write episode_ids")
        _ensure_unique(self.turning_points, name="personal model write turning_points")
        _ensure_unique(self.correction_refs, name="personal model write correction_refs")
        _ensure_unique(self.trigger_conditions, name="personal model write trigger_conditions")
        _ensure_unique(self.steps, name="personal model write steps")
        _ensure_unique(self.related_skill_ids, name="personal model write related_skill_ids")
        _ensure_unique(
            self.communication_preferences, name="personal model write communication_preferences"
        )
        _ensure_unique(self.autonomy_boundaries, name="personal model write autonomy_boundaries")


@dataclass(frozen=True, slots=True)
class PersonalModelGovernanceDecision:
    stored_maturity_state: str
    approval_state: str
    behavioral_state: str
    status: str
    reason: str
    proposal_type: str | None = None
    proposal_status: str | None = None


@dataclass(frozen=True, slots=True)
class PersonalModelWriteResult:
    status: str
    kind: str
    reason: str
    grounding: Grounding
    canonical_record: Record
    memory_entry: MemoryEntry
    proposal: ReflectionProposal | None = None
    observation: Observation | None = None
    fact: Fact | None = None

    @property
    def committed(self) -> bool:
        return self.status == "committed"


def evaluate_personal_model_governance(
    request: PersonalModelWriteRequest,
) -> PersonalModelGovernanceDecision:
    """Decide whether a write becomes a Fact (committed) or Observation (everything else).

    v5 collapses the three-state maturity into a two-state system.  The decision
    simply returns "committed" for user-directed/confirmed writes and
    "observed" otherwise.  "hypothesized" is legacy noise; if callers pass it,
    we treat it as "observed" because under v5, "observed" and "hypothesized"
    are the same row — both just Observations pending promotion.
    """

    if request.user_directed or request.user_confirmed:
        return PersonalModelGovernanceDecision(
            stored_maturity_state="committed",
            approval_state="approved",
            behavioral_state="active",
            status="committed",
            reason="explicit user memory is committed immediately",
        )

    candidate_class = str(request.metadata.get("memory_candidate_class") or "").strip().lower()
    if candidate_class in {"temporary_task", "draft_or_working_memory", "not_personal_model"}:
        return PersonalModelGovernanceDecision(
            stored_maturity_state="observed",
            approval_state="pending",
            behavioral_state="deferred",
            status="observed",
            reason=f"candidate gate kept {candidate_class} out of durable Personal Model facts",
        )

    # L1 opportunistic capture: chat LLM flagged something as worth noting.
    meta_lens = str(request.metadata.get("lens") or "").strip().lower()
    meta_signal_type = str(request.metadata.get("signal_type") or "").strip().lower()
    meta_stability = str(request.metadata.get("stability") or "").strip().lower()

    if (
        meta_lens in {"user_correction", "explicit_preference"}
        and request.confidence >= 0.65
        and request.conflict_state == "none"
        and request.sensitivity in {"low", "medium"}
    ):
        return PersonalModelGovernanceDecision(
            stored_maturity_state="committed",
            approval_state="approved",
            behavioral_state="active",
            status="committed",
            reason=f"user-directed signal ({meta_lens}) committed through fast learning",
        )

    # Rapport fast-promote: confident, explicit correction signals commit in-lane.
    if (
        request.kind in {"style", "relationship"}
        and request.confidence >= 0.80
        and request.conflict_state == "none"
        and not request.user_edited
    ):
        return PersonalModelGovernanceDecision(
            stored_maturity_state="committed",
            approval_state="approved",
            behavioral_state="active",
            status="committed",
            reason="rapport-lens fast-promote on high confidence",
        )

    if meta_signal_type == "correction_signal" and request.confidence >= 0.70:
        return PersonalModelGovernanceDecision(
            stored_maturity_state="committed",
            approval_state="approved",
            behavioral_state="active",
            status="committed",
            reason="correction signal committed through fast learning",
        )

    if meta_stability == "stable_trait" and request.confidence >= 0.75:
        return PersonalModelGovernanceDecision(
            stored_maturity_state="committed",
            approval_state="approved",
            behavioral_state="active",
            status="committed",
            reason="stable trait committed through fast learning",
        )

    # Everything else → Observation.
    return PersonalModelGovernanceDecision(
        stored_maturity_state="observed",
        approval_state="pending",
        behavioral_state="deferred",
        status="observed",
        reason="grounded signal stored as observation; awaiting consolidation",
    )


def _record_identity(
    kind: str,
    source_record_ids: tuple[str, ...],
    content: str,
    created_at: datetime | None,
) -> str:
    stamp = created_at.isoformat() if created_at is not None else ""
    return _capture_hash(kind, ",".join(source_record_ids), content, stamp)


def _component_metadata(
    request: PersonalModelWriteRequest,
    decision: PersonalModelGovernanceDecision,
    *,
    component_id: str,
) -> dict[str, str]:
    base = {
        "behavioral_state": decision.behavioral_state,
        "component_family": request.kind,
        "component_id": component_id,
        "policy_reason": decision.reason,
        "support_count": str(request.support_count),
        **dict(request.metadata),
    }
    return infer_recall_lifecycle_metadata(
        lens=str(base.get("lens") or _lens_for_kind(request.kind)),
        topic=str(base.get("topic") or base.get("sub_lens") or base.get("target_key") or ""),
        text=request.content,
        source=str(base.get("source") or base.get("observer_source") or ""),
        kind=request.kind,
        owner_scope="personal_model",
        metadata=base,
        now=request.created_at,
    ).metadata


def _lens_for_kind(kind: str) -> str:
    return _LEGACY_KIND_TO_LENS.get(kind, "knowledge")


def _derive_sub_lens(request: PersonalModelWriteRequest) -> str | None:
    """Choose a sub_lens hint from request metadata.  Free-form; no enum."""
    meta = request.metadata
    if "sub_lens" in meta:
        return str(meta["sub_lens"]) or None
    if request.kind == "style" and request.trait_signals:
        first = request.trait_signals[0]
        return f"big_five.{first.trait}" if first.trait in {
            "openness", "conscientiousness", "extraversion", "agreeableness",
            "neuroticism", "emotional_stability",
        } else None
    return None


def build_personal_model_component_record(
    request: PersonalModelWriteRequest,
    grounding: Grounding,
    decision: PersonalModelGovernanceDecision,
) -> Record:
    """Build a Record suitable for ``repository.upsert_record``.

    Under v5 the Record's ``layer_type`` is either ``personal_model_observation``
    or ``personal_model_fact`` depending on the decision.  The Record's
    payload mirrors the Observation/Fact fields.
    """
    if request.personal_model_id is None:
        raise ValueError("personal model component writes require personal_model_id")
    created_at = request.created_at or datetime.now(timezone.utc)
    identity = _record_identity(
        request.kind, request.source_record_ids, request.content.strip(), created_at
    )
    lens = _lens_for_kind(request.kind)
    sub_lens = _derive_sub_lens(request)
    component_id = f"pm:{decision.status}:{identity}"
    metadata = _component_metadata(request, decision, component_id=component_id)

    if decision.status == "committed":
        fact = Fact(
            fact_id=component_id,
            personal_model_id=request.personal_model_id,
            lens=lens,
            text=request.content.strip(),
            confidence=max(0.6, min(1.0, request.confidence or 0.8)),
            committed_at=created_at,
            source="user_explicit" if (request.user_directed or request.user_confirmed) else "pm_agent_promote",
            source_observation_ids=(),
            source_episode_ids=tuple(request.episode_ids),
            status="active",
            metadata=metadata,
        )
        payload = {
            "fact_id": fact.fact_id,
            "personal_model_id": fact.personal_model_id,
            "lens": fact.lens,
            "text": fact.text,
            "confidence": fact.confidence,
            "committed_at": fact.committed_at.isoformat(),
            "source": fact.source,
            "source_episode_ids": list(fact.source_episode_ids),
            "status": fact.status,
            "behavioral_state": decision.behavioral_state,
        }
        return Record(
            record_id=f"record:personal-model:fact:{identity}",
            kind="layer",
            schema_version="personal_model.fact/v1",
            owner_scope="personal_model",
            personal_model_id=request.personal_model_id,
            state_id=request.state_id,
            layer_type="personal_model_fact",
            created_at=created_at,
            payload=payload,
            metadata=metadata,
        )

    # Observation path.
    observation = Observation(
        observation_id=component_id,
        personal_model_id=request.personal_model_id,
        text=request.content.strip(),
        confidence=request.confidence or 0.5,
        episode_id=(request.episode_ids[0] if request.episode_ids else request.state_id or "unknown-episode"),
        last_seen_at=created_at,
        source="pm_agent_extract",
        lens=lens,
        sub_lens=sub_lens,
        direction=None,
        seen_count=max(1, request.support_count),
        captured_by_tool_call=False,
        status="active",
        metadata=metadata,
    )
    payload = {
        "observation_id": observation.observation_id,
        "personal_model_id": observation.personal_model_id,
        "lens": observation.lens,
        "sub_lens": observation.sub_lens,
        "text": observation.text,
        "confidence": observation.confidence,
        "episode_id": observation.episode_id,
        "last_seen_at": observation.last_seen_at.isoformat(),
        "source": observation.source,
        "seen_count": observation.seen_count,
        "status": observation.status,
        "behavioral_state": decision.behavioral_state,
    }
    return Record(
        record_id=f"record:personal-model:observation:{identity}",
        kind="layer",
        schema_version="personal_model.observation/v1",
        owner_scope="personal_model",
        personal_model_id=request.personal_model_id,
        state_id=request.state_id,
        layer_type="personal_model_observation",
        created_at=created_at,
        payload=payload,
        metadata=metadata,
    )


def build_personal_model_proposal(
    request: PersonalModelWriteRequest,
    grounding: Grounding,
    decision: PersonalModelGovernanceDecision,
    *,
    target_id: str,
) -> ReflectionProposal:
    if decision.proposal_type is None or decision.proposal_status is None:
        raise ValueError(
            "proposal build requires governance decision with proposal_type and proposal_status"
        )
    if request.personal_model_id is None:
        raise ValueError("personal model proposal writes require personal_model_id")
    created_at = request.created_at
    identity = _record_identity(
        f"{request.kind}:{decision.proposal_type}",
        request.source_record_ids,
        request.content.strip(),
        created_at,
    )
    proposal_kind = decision.proposal_type
    reason = decision.reason
    return ReflectionProposal(
        reflection_proposal_id=f"proposal:personal-model:{proposal_kind}:{identity}",
        owner_scope="personal_model",
        proposal_type=proposal_kind,
        content=f"{request.kind} reflection requires review: {reason}",
        grounding_ids=(grounding.grounding_id,),
        personal_model_id=request.personal_model_id,
        state_id=request.state_id,
        target_id=target_id,
        status=decision.proposal_status,
        created_at=created_at,
        updated_at=created_at,
        metadata={
            "requested_maturity_state": request.maturity_state,
            "stored_maturity_state": decision.stored_maturity_state,
            "support_count": str(request.support_count),
            **dict(request.metadata),
        },
    )


__all__ = [name for name in globals() if not name.startswith("__")]
