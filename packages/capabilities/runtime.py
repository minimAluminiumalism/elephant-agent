"""Extension and capability contracts.

These are thin ports that allow the kernel and feature packages to evolve in
parallel. They intentionally avoid provider-specific behavior and only define
what the runtime expects from a capability.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Mapping, Protocol, runtime_checkable

from packages.contracts import Episode
from packages.contracts.runtime import (
    ContextBundle,
    ExecutionResult,
    StateFocusDecision,
    MemoryRecord,
    RuntimeModelChoice,
    PersonalModelRuntimeState,
)


@dataclass(frozen=True, slots=True)
class CapabilityDescriptor:
    capability_id: str
    kind: str
    version: str
    dependencies: tuple[str, ...] = ()
    config_schema: Mapping[str, Any] = field(default_factory=dict)
    metadata: Mapping[str, Any] = field(default_factory=dict)
    enabled: bool = True


@dataclass(frozen=True, slots=True)
class CapabilityHealth:
    status: str
    detail: str | None = None
    checked_at: datetime | None = None


@runtime_checkable
class CapabilityRegistry(Protocol):
    def register(self, descriptor: CapabilityDescriptor) -> None:
        """Register a capability descriptor."""

    def get(self, capability_id: str) -> CapabilityDescriptor | None:
        """Return the active descriptor for a capability if it exists."""

    def list(self) -> tuple[CapabilityDescriptor, ...]:
        """Return all registered capability descriptors."""


@runtime_checkable
class MemoryCapability(Protocol):
    descriptor: CapabilityDescriptor

    def record(self, memory: MemoryRecord) -> None:
        """Persist a memory record."""

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
        """Search memories for a session or an explicit recovery scope."""


@runtime_checkable
class ContextCapability(Protocol):
    descriptor: CapabilityDescriptor

    def assemble(
        self,
        session: Episode,
        work_items: tuple[object, ...],
        memories: tuple[MemoryRecord, ...],
        *,
        state_focus: StateFocusDecision | None = None,
    ) -> ContextBundle:
        """Assemble the active context bundle."""


@runtime_checkable
class ModelProviderCapability(Protocol):
    descriptor: CapabilityDescriptor

    def selection_state(self) -> RuntimeModelChoice:
        """Return the currently configured strong/weak model pair plus state_focus mode."""

    def generate(
        self,
        *,
        profile: PersonalModelRuntimeState,
        session: Episode,
        context: ContextBundle,
        prompt: str,
        model_role: str = "strong",
    ) -> ExecutionResult:
        """Generate the next model-backed execution result for the requested model role."""


@runtime_checkable
class AuthProviderCapability(Protocol):
    descriptor: CapabilityDescriptor

    def resolve(self, provider_id: str) -> Mapping[str, str]:
        """Resolve an auth payload for a provider."""


@runtime_checkable
class ToolCapability(Protocol):
    descriptor: CapabilityDescriptor

    def invoke(
        self,
        tool_name: str,
        arguments: Mapping[str, Any],
        *,
        session_id: str,
    ) -> ExecutionResult:
        """Invoke a side-effecting tool."""


@runtime_checkable
class SkillCapability(Protocol):
    descriptor: CapabilityDescriptor

    def activate(self, skill_name: str, *, session_id: str) -> None:
        """Activate a procedural skill for a session."""


@runtime_checkable
class DeliveryAdapterCapability(Protocol):
    descriptor: CapabilityDescriptor

    def deliver(
        self,
        session_id: str,
        payload: Mapping[str, Any],
    ) -> ExecutionResult:
        """Deliver a message or event to an external surface."""


@runtime_checkable
class StorageBackendCapability(Protocol):
    descriptor: CapabilityDescriptor

    def write(self, record: object) -> None:
        """Persist a contract-shaped record."""

    def read(self, record_type: str, record_id: str) -> object | None:
        """Read a record from storage."""


@runtime_checkable
class TelemetrySinkCapability(Protocol):
    descriptor: CapabilityDescriptor

    def emit(self, event: Mapping[str, Any]) -> None:
        """Emit an auditable telemetry event."""
