"""Tests for lifecycle metadata on PersonalModelWriteRequest promotion path."""

from __future__ import annotations

from datetime import datetime, timezone

from packages.contracts import Grounding
from packages.evidence import PersonalModelWriteRequest
from packages.evidence.personal_model_support import (
    build_personal_model_component_record,
    evaluate_personal_model_governance,
)

_NOW = datetime(2026, 5, 8, 10, 0, tzinfo=timezone.utc)


def test_component_record_and_memory_metadata_receive_lifecycle_defaults() -> None:
    request = PersonalModelWriteRequest(
        kind="knowledge",
        content="小红书账号约20条笔记，399赞藏，10+粉丝。",
        source_record_ids=("record:source",),
        personal_model_id="you",
        maturity_state="committed",
        confidence=0.9,
        user_confirmed=True,
        metadata={"topic": "xiaohongshu.profile.positioning", "recall_policy": "review"},
        created_at=_NOW,
    )
    decision = evaluate_personal_model_governance(request)
    record = build_personal_model_component_record(
        request,
        Grounding(
            grounding_id="grounding:test",
            source_record_ids=("record:source",),
            confidence=1.0,
            created_at=_NOW,
        ),
        decision,
    )

    assert record.metadata["recall_policy"] == "review"
    assert record.metadata["recall_policy_source"] == "explicit"
    assert record.metadata["memory_lifecycle"] == "review"
    assert record.metadata["last_verified_at"] == _NOW.isoformat()
    assert record.metadata["review_after_days"] == "14"
    assert record.metadata["lifecycle_inferred"] == "false"


def test_candidate_gate_keeps_draft_working_memory_out_of_committed_facts() -> None:
    request = PersonalModelWriteRequest(
        kind="knowledge",
        content="今晚尼泊尔小象短帖的一个工作草稿。",
        source_record_ids=("record:resume",),
        personal_model_id="you",
        maturity_state="committed",
        confidence=0.9,
        metadata={
            "lens": "explicit_preference",
            "signal_type": "explicit_preference",
            "memory_candidate_class": "draft_or_working_memory",
        },
        created_at=_NOW,
    )

    decision = evaluate_personal_model_governance(request)

    assert decision.status == "observed"
    assert decision.stored_maturity_state == "observed"
    assert "candidate gate" in decision.reason
