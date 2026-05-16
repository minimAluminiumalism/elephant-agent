"""Recall evidence inspection methods for the API runtime app."""

from __future__ import annotations

from typing import Any


def inspect_recall_evidence(self, episode_id: str, evidence_ref: str) -> dict[str, Any]:
    evidence = self.recall_runtime.store.get(evidence_ref)
    if evidence is None or evidence.episode_id != episode_id:
        raise KeyError(evidence_ref)
    return {
        "episode_id": episode_id,
        "evidence": evidence,
        "state": self.recall_runtime.store.state(evidence_ref),
        "lineage": self.recall_runtime.store.lineage(evidence_ref),
    }
