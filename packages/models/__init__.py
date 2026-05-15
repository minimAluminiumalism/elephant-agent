"""Provider-neutral model adapter interfaces and baseline adapters."""

from __future__ import annotations

from importlib import import_module
import sys
from typing import TYPE_CHECKING

from .auth_headers import (
    AuthHeaderContext,
    AuthHeaderStrategy,
    InMemoryAuthHeaderStrategyRegistry,
    build_provider_auth_headers,
    default_auth_header_strategy_registry,
)
from .bootstrap import (
    EmbeddingBootstrapState,
    load_embedding_bootstrap_state,
    persist_embedding_bootstrap_state,
    resolve_embedding_bootstrap_state,
    run_embedding_bootstrap_worker,
    trigger_embedding_bootstrap,
)
from .inventory import MODEL_SURFACES
from .model_metadata import (
    ResolvedModelMetadata,
    get_cached_context_length,
    resolve_provider_model_metadata,
    save_context_length,
)
from .provider_runtime import (
    InMemoryProviderManifestRegistry,
    InMemoryProviderTransportRegistry,
    ProviderCatalogRecord,
    ProviderManifest,
    ProviderManifestRegistry,
    ProviderRuntimeResolution,
    ProviderRuntimeResolver,
    ProviderSetupGuide,
    ProviderTransportDefinition,
    ProviderTransportRegistry,
)
from .runtime import (
    CredentialSource,
    InMemoryModelAdapterRegistry,
    ModelAdapter,
    ModelAdapterDescriptor,
    ModelEmbeddingResult,
    ModelRequest,
    ModelTextResult,
    ModelUsage,
    PreviewModelProviderCapability,
    PromptEchoModelAdapter,
    StaticTextModelAdapter,
)

if TYPE_CHECKING:
    from .discovery import (
        DiscoveredProviderModel,
        DiscoveredProviderState,
        ProviderMetadataDiscoveryService,
        ProviderMetadataProbe,
        ProviderMetadataProbeRegistry,
        ProviderStateEvaluator,
        heuristic_context_window,
        request_json,
    )
    from .runtime_capability import SurfaceModelProviderCapability

_LAZY_EXPORT_MODULES = {
    "DiscoveredProviderModel": ".discovery",
    "DiscoveredProviderState": ".discovery",
    "ProviderMetadataDiscoveryService": ".discovery",
    "ProviderMetadataProbe": ".discovery",
    "ProviderMetadataProbeRegistry": ".discovery",
    "ProviderStateEvaluator": ".discovery",
    "heuristic_context_window": ".discovery",
    "request_json": ".discovery",
    "SurfaceModelProviderCapability": ".runtime_capability",
}


def _load_lazy_exports(module_path: str) -> None:
    module = import_module(module_path, __name__)
    for export_name, export_module in _LAZY_EXPORT_MODULES.items():
        if export_module == module_path:
            globals()[export_name] = getattr(module, export_name)


def _load_discovery_exports() -> None:
    _load_lazy_exports(".discovery")


_auth_runtime = sys.modules.get("packages.auth.runtime")
if _auth_runtime is None or hasattr(_auth_runtime, "AuthProfile"):
    _load_lazy_exports(".discovery")


def __getattr__(name: str):
    module_path = _LAZY_EXPORT_MODULES.get(name)
    if module_path is not None:
        _load_lazy_exports(module_path)
        return globals()[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "AuthHeaderContext",
    "AuthHeaderStrategy",
    "CredentialSource",
    "DiscoveredProviderModel",
    "DiscoveredProviderState",
    "EmbeddingBootstrapState",
    "InMemoryAuthHeaderStrategyRegistry",
    "InMemoryProviderManifestRegistry",
    "InMemoryProviderTransportRegistry",
    "InMemoryModelAdapterRegistry",
    "MODEL_SURFACES",
    "ModelAdapter",
    "ModelAdapterDescriptor",
    "ModelEmbeddingResult",
    "ModelRequest",
    "ModelTextResult",
    "ModelUsage",
    "ProviderCatalogRecord",
    "ProviderManifest",
    "ProviderManifestRegistry",
    "ProviderMetadataDiscoveryService",
    "ProviderMetadataProbe",
    "ProviderMetadataProbeRegistry",
    "ProviderRuntimeResolution",
    "ProviderRuntimeResolver",
    "ProviderSetupGuide",
    "ProviderStateEvaluator",
    "ProviderTransportDefinition",
    "ProviderTransportRegistry",
    "PreviewModelProviderCapability",
    "PromptEchoModelAdapter",
    "ResolvedModelMetadata",
    "StaticTextModelAdapter",
    "SurfaceModelProviderCapability",
    "build_provider_auth_headers",
    "default_auth_header_strategy_registry",
    "get_cached_context_length",
    "heuristic_context_window",
    "load_embedding_bootstrap_state",
    "persist_embedding_bootstrap_state",
    "resolve_embedding_bootstrap_state",
    "request_json",
    "resolve_provider_model_metadata",
    "run_embedding_bootstrap_worker",
    "save_context_length",
    "trigger_embedding_bootstrap",
]
