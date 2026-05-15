"""Tests for conservative recall lifecycle metadata inference."""

from __future__ import annotations

from datetime import datetime, timezone

from packages.evidence import infer_recall_lifecycle_metadata

_NOW = datetime(2026, 5, 8, 10, 0, tzinfo=timezone.utc)


def test_agent_policy_marks_changeable_memory_as_review() -> None:
    result = infer_recall_lifecycle_metadata(
        lens="knowledge",
        topic="xiaohongshu.profile.positioning",
        text="小红书账号约20条笔记，399赞藏，10+粉丝。",
        source="user_said",
        kind="personal_model_claim",
        metadata={"recall_policy": "review"},
        now=_NOW,
    )

    assert result.lifecycle == "review"
    assert result.metadata["memory_lifecycle"] == "review"
    assert result.metadata["last_verified_at"] == _NOW.isoformat()
    assert result.metadata["review_after_days"] == "14"
    assert result.metadata["lifecycle_inferred"] == "false"
    assert result.metadata["recall_policy_source"] == "explicit"


def test_rapport_preference_stays_preference_without_review_clock() -> None:
    result = infer_recall_lifecycle_metadata(
        lens="rapport",
        topic="assistant.answer.style",
        text="User prefers concise answers.",
        source="user_said",
        kind="personal_model_claim",
        now=_NOW,
    )

    assert result.lifecycle == "preference"
    assert result.metadata["memory_lifecycle"] == "preference"
    assert "last_verified_at" not in result.metadata
    assert "review_after_days" not in result.metadata


def test_agent_policy_marks_short_lived_plan_as_temporal() -> None:
    result = infer_recall_lifecycle_metadata(
        lens="chapter",
        topic="work.publish.plan",
        text="今晚准备把这篇内容发到小红书。",
        source="learned",
        kind="personal_model_claim",
        metadata={"recall_policy": "temporary"},
        now=_NOW,
    )

    assert result.lifecycle == "temporal"
    assert result.metadata["review_after_days"] == "3"


def test_knowledge_without_agent_policy_defaults_to_stable_not_keyword_guess() -> None:
    result = infer_recall_lifecycle_metadata(
        lens="knowledge",
        topic="xiaohongshu.profile.positioning",
        text="小红书账号约20条笔记，399赞藏，10+粉丝。",
        source="user_said",
        kind="personal_model_claim",
        now=_NOW,
    )

    assert result.metadata["recall_policy"] == "stable"
    assert result.metadata["recall_policy_source"] == "structural_default"
    assert result.metadata["memory_lifecycle"] == "preference"
    assert "last_verified_at" not in result.metadata


def test_explicit_lifecycle_is_preserved() -> None:
    result = infer_recall_lifecycle_metadata(
        lens="knowledge",
        topic="misc.anything.value",
        text="Some status-like text with followers.",
        metadata={"memory_lifecycle": "permanent", "review_after_days": "90"},
        now=_NOW,
    )

    assert result.lifecycle == "permanent"
    assert result.inferred is False
    assert result.metadata["memory_lifecycle"] == "permanent"
    assert result.metadata["review_after_days"] == "90"
