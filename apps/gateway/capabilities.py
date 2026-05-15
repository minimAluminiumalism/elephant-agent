"""Gateway capability adapters and provider bridges."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import replace
from typing import Any
from uuid import uuid4

from packages.models import SurfaceModelProviderCapability
from packages.auth import AuthProfile
from packages.capabilities.runtime import (
    CapabilityDescriptor,
    ContextCapability,
    MemoryCapability,
    ModelProviderCapability,
    TelemetrySinkCapability,
)
from packages.context import ContextRuntime
from packages.contracts import Episode
from packages.contracts.runtime import (
    ContextBundle,
    EvidenceRetrievalRequest,
    EvidenceRetrievalResult,
    ExecutionResult,
    StateFocusDecision,
    MemoryRecord,
    PersonalModelRuntimeState,
)
from packages.evidence import MemoryRuntime
from packages.state import LoadedProfile, build_prompt_contract
from packages.storage import RuntimeStorageRepository


class GatewayTelemetrySink(TelemetrySinkCapability):
    def __init__(self) -> None:
        self.descriptor = CapabilityDescriptor(
            capability_id="gateway.telemetry",
            kind="telemetry_sink",
            version="1.0.0",
            metadata={"description": "In-process telemetry sink for gateway shared-runtime turns."},
        )
        self._events: list[dict[str, Any]] = []

    @property
    def events(self) -> tuple[dict[str, Any], ...]:
        return tuple(self._events)

    def emit(self, event: Mapping[str, Any]) -> None:
        self._events.append(dict(event))


class GatewayMemoryCapability(MemoryCapability):
    def __init__(self, runtime: MemoryRuntime) -> None:
        self.descriptor = CapabilityDescriptor(
            capability_id="gateway.memory",
            kind="memory",
            version="1.0.0",
            metadata={"description": "Shared memory adapter for gateway turns."},
        )
        self.runtime = runtime

    def record(self, memory: MemoryRecord) -> None:
        self.runtime.store.upsert(memory)

    def retrieve_evidence(self, request: EvidenceRetrievalRequest) -> EvidenceRetrievalResult:
        return self.runtime.retrieve_evidence(request)

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
        result = self.runtime.retrieve(
            session_id,
            query,
            work_item_ids=work_item_ids,
            scope_episode_ids=scope_episode_ids or scope_session_ids,
            scope_reason=scope_reason,
        )
        return tuple(candidate.record for candidate in result.candidates)


class GatewayContextCapability(ContextCapability):
    def __init__(self, profile: LoadedProfile, *, total_tokens: int = 3072) -> None:
        self.prompt_contract = build_prompt_contract(profile, prompt_mode="full")
        self.descriptor = CapabilityDescriptor(
            capability_id="gateway.context",
            kind="context",
            version="1.0.0",
            metadata={"description": "Prompt-contract-aware context adapter for gateway turns."},
        )
        self.runtime = ContextRuntime(
            instruction_refs=self.prompt_contract.instruction_refs,
            total_tokens=total_tokens,
        )

    def assemble(
        self,
        session: Episode,
        work_items: tuple[object, ...],
        memories: tuple[MemoryRecord, ...],
        *,
        state_focus: StateFocusDecision | None = None,
    ) -> ContextBundle:
        bundle = self.runtime.assemble(session, work_items, memories, state_focus=state_focus)
        return replace(
            bundle,
            bundle_id=f"bundle:{session.episode_id}:{len(work_items)}:{len(memories)}",
            instruction_refs=self.prompt_contract.instruction_refs,
        )


class GatewayPreviewModelProvider(ModelProviderCapability):
    def __init__(self) -> None:
        self.descriptor = CapabilityDescriptor(
            capability_id="gateway.model.preview",
            kind="model_provider",
            version="1.0.0",
            metadata={"description": "Deterministic conversational fallback for gateway turns."},
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
        summary = "Gateway model provider is not configured; configure a model provider before chatting through IM."
        return ExecutionResult(
            execution_id=f"gateway.model:{session.episode_id}:{uuid4().hex}",
            episode_id=session.episode_id,
            outcome="ok",
            summary=summary,
            side_effects=("gateway-preview-provider", profile.mode),
        )


class GatewaySurfaceModelProvider(ModelProviderCapability):
    def __init__(
        self,
        *,
        repository: RuntimeStorageRepository,
        fallback: ModelProviderCapability,
        active_provider_profile: AuthProfile | None,
    ) -> None:
        profile_id = active_provider_profile.profile_id if active_provider_profile is not None else None
        provider_id = active_provider_profile.provider_id if active_provider_profile is not None else None
        self.surface = SurfaceModelProviderCapability(
            repository=repository,
            secret_key_path=repository.database_path.parent / "provider-secrets.key",
            fallback=fallback,
            active_provider_profile_id=profile_id,
            active_provider_id=provider_id,
            capability_id="gateway.model.runtime",
            surface_label="gateway",
        )
        self.descriptor = self.surface.descriptor
        self.fallback = fallback

    def describe(self) -> Mapping[str, object]:
        return self.surface.describe()

    def selection_state(self) -> RuntimeModelChoice:
        return self.surface.selection_state()

    def turn_scoped_recall_blocks(
        self,
        *,
        profile: PersonalModelRuntimeState,
        session: Episode,
        context: ContextBundle,
        prompt: str,
    ) -> tuple[str, ...]:
        return self.surface.turn_scoped_recall_blocks(
            profile=profile,
            session=session,
            context=context,
            prompt=prompt,
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
        try:
            return self.surface.generate(
                profile=profile,
                session=session,
                context=context,
                prompt=prompt,
                model_role=model_role,
            )
        except LookupError:
            return self.fallback.generate(
                profile=profile,
                session=session,
                context=context,
                prompt=prompt,
                model_role=model_role,
            )
