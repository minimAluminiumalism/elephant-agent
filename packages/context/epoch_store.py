"""Epoch persistence — file-based storage for SessionContextEpoch.

Replaces the legacy Record-based persistence that was broken when the records
table was removed from the clean storage schema. Both CLI and Gateway use this store.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Protocol

from .session_projection import (
    SessionContextEpoch,
    restore_session_context_epoch,
    session_context_epoch_payload,
)


class EpochStore(Protocol):
    """Protocol for loading and saving session context epochs."""

    def load(self, session_id: str) -> SessionContextEpoch | None: ...
    def save(self, epoch: SessionContextEpoch) -> None: ...


class FileEpochStore:
    """Stores epochs as JSON files in <state_dir>/.epochs/<safe_id>.json."""

    def __init__(self, state_dir: Path) -> None:
        self._dir = state_dir / ".epochs"

    def load(self, session_id: str) -> SessionContextEpoch | None:
        path = self._path(session_id)
        try:
            with open(path, "r", encoding="utf-8") as handle:
                data = json.load(handle)
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            return None
        if not isinstance(data, dict):
            return None
        return restore_session_context_epoch(data, session_id=session_id)

    def save(self, epoch: SessionContextEpoch) -> None:
        self._dir.mkdir(parents=True, exist_ok=True)
        path = self._path(epoch.session_id)
        payload = session_context_epoch_payload(epoch)
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, separators=(",", ":"), ensure_ascii=False)

    def _path(self, session_id: str) -> Path:
        safe_id = session_id.replace("/", "_").replace(":", "_").replace(" ", "_")
        return self._dir / f"{safe_id}.json"


class InMemoryEpochStore:
    """In-memory epoch store for tests."""

    def __init__(self) -> None:
        self._store: dict[str, SessionContextEpoch] = {}

    def load(self, session_id: str) -> SessionContextEpoch | None:
        return self._store.get(session_id)

    def save(self, epoch: SessionContextEpoch) -> None:
        self._store[epoch.session_id] = epoch
