"""Inbound message serialization primitives for gateway adapters."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import TypeVar


T = TypeVar("T")


@dataclass(slots=True)
class _SequencerEntry:
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    ref_count: int = 0


class InboundSequencer:
    """Serialize inbound handling for the same account/conversation key.

    Gateway adapters can keep their receive fan-out model (for example, a long-poll
    loop that creates one task per inbound payload) while still making the actual
    message handling semantics explicit and deterministic per conversation.
    """

    def __init__(self) -> None:
        self._entries: dict[str, _SequencerEntry] = {}
        self._entries_guard = asyncio.Lock()

    @staticmethod
    def key_for(*, account_id: str, conversation_id: str) -> str:
        resolved_account_id = str(account_id or "").strip()
        resolved_conversation_id = str(conversation_id or "").strip()
        if not resolved_account_id:
            raise ValueError("account_id is required for inbound sequencing")
        if not resolved_conversation_id:
            raise ValueError("conversation_id is required for inbound sequencing")
        return f"{resolved_account_id}:{resolved_conversation_id}"

    @property
    def tracked_key_count(self) -> int:
        """Return the number of conversation keys currently tracked.

        Intended for diagnostics and tests; adapters should normally only use
        :meth:`run_serialized`.
        """

        return len(self._entries)

    async def run_serialized(
        self,
        key: str,
        coro_factory: Callable[[], Awaitable[T]],
    ) -> T:
        """Run ``coro_factory`` under the FIFO lock for ``key``."""

        resolved_key = str(key or "").strip()
        if not resolved_key:
            raise ValueError("inbound sequencer key must not be empty")
        entry = await self._claim_entry(resolved_key)
        try:
            async with entry.lock:
                return await coro_factory()
        finally:
            await self._release_entry(resolved_key)

    async def _claim_entry(self, key: str) -> _SequencerEntry:
        async with self._entries_guard:
            entry = self._entries.get(key)
            if entry is None:
                entry = _SequencerEntry()
                self._entries[key] = entry
            entry.ref_count += 1
            return entry

    async def _release_entry(self, key: str) -> None:
        async with self._entries_guard:
            entry = self._entries.get(key)
            if entry is None:
                return
            entry.ref_count -= 1
            if entry.ref_count <= 0:
                self._entries.pop(key, None)


__all__ = ["InboundSequencer"]
