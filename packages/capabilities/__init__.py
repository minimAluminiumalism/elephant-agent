"""Capability contracts and registry primitives for Elephant Agent."""

from .inventory import CAPABILITY_SURFACES
from .runtime import (
    AuthProviderCapability,
    CapabilityDescriptor,
    CapabilityHealth,
    CapabilityRegistry,
    ContextCapability,
    DeliveryAdapterCapability,
    MemoryCapability,
    ModelProviderCapability,
    SkillCapability,
    StorageBackendCapability,
    TelemetrySinkCapability,
    ToolCapability,
)

__all__ = [
    "AuthProviderCapability",
    "CAPABILITY_SURFACES",
    "CapabilityDescriptor",
    "CapabilityHealth",
    "CapabilityRegistry",
    "ContextCapability",
    "DeliveryAdapterCapability",
    "MemoryCapability",
    "ModelProviderCapability",
    "SkillCapability",
    "StorageBackendCapability",
    "TelemetrySinkCapability",
    "ToolCapability",
]
