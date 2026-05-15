"""Memory governance methods for the API runtime app."""

from __future__ import annotations

from typing import Any


def inspect_memory(self, session_id: str, memory_id: str) -> dict[str, Any]:
    memory = self.memory_runtime.store.get(memory_id)
    if memory is None or memory.episode_id != session_id:
        raise KeyError(memory_id)
    return {
        "episode_id": session_id,
        "session_id": session_id,
        "memory": memory,
        "memory_state": self.memory_runtime.store.state(memory_id),
        "memory_lineage": self.memory_runtime.store.lineage(memory_id),
    }


def correct_memory(
    self,
    session_id: str,
    memory_id: str,
    *,
    corrected_content: str,
    reason: str = "",
    actor: str = "user",
) -> dict[str, Any]:
    result = self.memory_runtime.correct_memory(memory_id, corrected_content, actor=actor, reason=reason)
    if result.decision.target_memory_id is None:
        raise KeyError(memory_id)
    original = self.memory_runtime.store.get(memory_id)
    if original is None or original.episode_id != session_id:
        raise KeyError(memory_id)
    return {
        "episode_id": session_id,
        "session_id": session_id,
        "decision": result.decision,
        "memory": result.record,
        "memory_state": self.memory_runtime.store.state(memory_id),
        "memory_lineage": self.memory_runtime.store.lineage(memory_id),
    }


def delete_memory(
    self,
    session_id: str,
    memory_id: str,
    *,
    reason: str,
    actor: str = "user",
) -> dict[str, Any]:
    original = self.memory_runtime.store.get(memory_id)
    if original is None or original.episode_id != session_id:
        raise KeyError(memory_id)
    result = self.memory_runtime.delete_memory(memory_id, actor=actor, reason=reason)
    return {
        "episode_id": session_id,
        "session_id": session_id,
        "decision": result.decision,
        "memory": original,
        "memory_state": self.memory_runtime.store.state(memory_id),
        "memory_lineage": self.memory_runtime.store.lineage(memory_id),
    }


def pin_memory(
    self,
    session_id: str,
    memory_id: str,
    *,
    pinned: bool,
    reason: str = "",
    actor: str = "user",
) -> dict[str, Any]:
    original = self.memory_runtime.store.get(memory_id)
    if original is None or original.episode_id != session_id:
        raise KeyError(memory_id)
    result = (
        self.memory_runtime.pin_memory(memory_id, actor=actor, reason=reason)
        if pinned
        else self.memory_runtime.unpin_memory(memory_id, actor=actor, reason=reason)
    )
    record = result.record
    if record is None:
        raise RuntimeError(result.decision.reason)
    return {
        "episode_id": session_id,
        "session_id": session_id,
        "decision": result.decision,
        "memory": record,
        "memory_state": self.memory_runtime.store.state(memory_id),
        "memory_lineage": self.memory_runtime.store.lineage(memory_id),
    }
