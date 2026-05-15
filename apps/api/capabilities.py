"""API capability adapters and deterministic preview providers."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import replace
from typing import Any
from uuid import uuid4

from packages.capabilities.runtime import (
    CapabilityDescriptor,
    ContextCapability,
    DeliveryAdapterCapability,
    MemoryCapability,
    ModelProviderCapability,
    TelemetrySinkCapability,
    ToolCapability,
)
from packages.context import (
    ContextRuntime,
    apply_session_context_epoch,
)
from packages.context.epoch_store import FileEpochStore
from packages.context.compress import compress_epoch
from packages.contracts import (
    ContextBundle,
    Episode,
    ExecutionResult,
    MemoryRecord,
)
from packages.contracts.runtime import (
    StateFocusDecision,
    PersonalModelRuntimeState,
)
from packages.evidence import MemoryRuntime
from packages.storage import RuntimeStorageRepository
from packages.skills import SkillPromptContextBuilder
from packages.tools import ToolRuntime


class APITelemetrySink(TelemetrySinkCapability):
    def __init__(self) -> None:
        self.descriptor = CapabilityDescriptor(
            capability_id="api.telemetry",
            kind="telemetry_sink",
            version="1.0.0",
            metadata={"description": "In-process telemetry sink for API wiring."},
        )
        self._events: list[dict[str, Any]] = []

    @property
    def events(self) -> tuple[dict[str, Any], ...]:
        return tuple(self._events)

    def emit(self, event: Mapping[str, Any]) -> None:
        self._events.append(dict(event))


class APIMemoryCapability(MemoryCapability):
    def __init__(self, store: MemoryRuntime) -> None:
        self.descriptor = CapabilityDescriptor(
            capability_id="api.memory",
            kind="memory",
            version="1.0.0",
            metadata={"description": "Memory adapter for API-backed kernel flows."},
        )
        self.store = store

    def record(self, memory: MemoryRecord) -> None:
        self.store.store.upsert(memory)

    def search(
        self,
        session_id: str,
        query: str,
        *,
        work_item_ids: tuple[str, ...] = (),
        scope_session_ids: tuple[str, ...] = (),
        scope_episode_ids: tuple[str, ...] = (),
        scope_reason: str = "",
    ) -> tuple[MemoryRecord, ...]:
        resolved_scope_episode_ids = scope_episode_ids or scope_session_ids
        result = self.store.retrieve(
            session_id,
            query,
            work_item_ids=work_item_ids,
            scope_episode_ids=resolved_scope_episode_ids,
            scope_reason=scope_reason,
        )
        return tuple(candidate.record for candidate in result.candidates)


class APIContextCapability(ContextCapability):
    def __init__(
        self,
        runtime: ContextRuntime,
        *,
        skill_prompt_context: SkillPromptContextBuilder | None = None,
        repository: RuntimeStorageRepository | None = None,
    ) -> None:
        self.descriptor = CapabilityDescriptor(
            capability_id="api.context",
            kind="context",
            version="1.0.0",
            metadata={"description": "Layered context adapter for API flows."},
        )
        self.runtime = runtime
        self.skill_prompt_context = skill_prompt_context
        self.repository = repository
        self._last_session_id: str | None = None

    def assemble(
        self,
        session: Episode,
        work_items: tuple[object, ...],
        memories: tuple[MemoryRecord, ...],
        *,
        state_focus: StateFocusDecision | None = None,
    ) -> ContextBundle:
        self._last_session_id = session.episode_id
        runtime = self.runtime
        if self.skill_prompt_context is not None:
            skill_lines = self.skill_prompt_context.stable_prefix_lines(session)
            if skill_lines:
                runtime = ContextRuntime(
                    instruction_refs=(*self.runtime.instruction_refs, *skill_lines),
                    total_tokens=self.runtime.total_tokens,
                )
        bundle = runtime.assemble(session, work_items, memories, state_focus=state_focus)
        bundle = replace(bundle, instruction_refs=runtime.instruction_refs)
        _epoch_store = FileEpochStore(self.repository.database_path.parent) if self.repository is not None else None
        epoch = _epoch_store.load(session.episode_id) if _epoch_store is not None else None
        return apply_session_context_epoch(bundle, epoch)

    def force_projection_compaction(
        self,
        *,
        reason: str = "provider-overflow",
        session_id: str | None = None,
    ):
        resolved_session_id = session_id or self._last_session_id
        if self.repository is None or not resolved_session_id:
            return None
        _epoch_store = FileEpochStore(self.repository.database_path.parent)
        epoch = _epoch_store.load(resolved_session_id)
        if epoch is None or not epoch.frozen:
            return None
        result = compress_epoch(
            epoch,
            context_limit=self.runtime.total_tokens,
            usage_tokens=self.runtime.total_tokens,
            reflect_compressor=None,
        )
        if result is not None:
            updated, _compress_result = result
            _epoch_store.save(updated)
            return _compress_result
        return None

    def flush_projection_memory(self) -> None:
        return None


class APIDeliveryCapability(DeliveryAdapterCapability):
    def __init__(self) -> None:
        self.descriptor = CapabilityDescriptor(
            capability_id="api.delivery",
            kind="delivery",
            version="1.0.0",
            metadata={"description": "Delivery adapter for API controlled execution."},
        )

    def deliver(self, session_id: str, payload: Mapping[str, Any]) -> ExecutionResult:
        summary = str(payload.get("summary", "delivered response"))
        return ExecutionResult(
            execution_id=f"delivery:{session_id}:{uuid4().hex}",
            episode_id=session_id,
            outcome="ok",
            summary=summary,
            side_effects=("delivery",),
        )


class APIModelProvider(ModelProviderCapability):
    def __init__(self) -> None:
        self.descriptor = CapabilityDescriptor(
            capability_id="api.model",
            kind="model_provider",
            version="1.0.0",
            metadata={"description": "Deterministic model adapter for API flows."},
        )

    def generate(
        self,
        *,
        profile: PersonalModelRuntimeState,
        session: Episode,
        context: ContextBundle,
        prompt: str,
        model_role: str = "strong",
    ) -> ExecutionResult:
        summary = prompt.strip() or "acknowledged"
        if context.rendered_prompt:
            summary = f"{summary} | context: {context.rendered_prompt.splitlines()[0]}"
        return ExecutionResult(
            execution_id=f"model:{session.episode_id}:{uuid4().hex}",
            episode_id=session.episode_id,
            outcome="ok",
            summary=summary,
            side_effects=(profile.mode, f"model_role={model_role}"),
        )


class APIToolExecution(ToolCapability):
    def __init__(self, runtime: ToolRuntime) -> None:
        self.descriptor = CapabilityDescriptor(
            capability_id="api.tools",
            kind="tool",
            version="1.0.0",
            metadata={"description": "API tool runtime."},
        )
        self.runtime = runtime

    def invoke(
        self,
        tool_name: str,
        arguments: Mapping[str, Any],
        *,
        session_id: str,
    ) -> ExecutionResult:
        return self.runtime.invoke(tool_name, arguments, session_id=session_id)
