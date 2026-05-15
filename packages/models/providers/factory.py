"""Provider adapter factory helpers.

These helpers keep runtime adapter selection package-owned so product surfaces
can stay thin and declarative while still allowing registry-based extension.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from packages.auth.runtime import AuthProfile
from packages.models.provider_runtime import ProviderRuntimeResolver
from packages.models.runtime import CredentialSource, ModelAdapter

from .registry import (
    ModelAdapterBuildContext,
    default_model_adapter_builder_registry,
)


@dataclass(frozen=True, slots=True)
class PinnedCredentialSource(CredentialSource):
    provider_id: str
    values: Mapping[str, str]

    def resolve(self, provider_id: str) -> Mapping[str, str]:
        if provider_id != self.provider_id:
            raise LookupError(f"missing pinned credentials for provider: {provider_id}")
        return dict(self.values)


def build_model_adapter(
    profile: AuthProfile,
    *,
    runtime_resolver: ProviderRuntimeResolver,
    credentials: Mapping[str, str],
    adapter_id: str,
    stream_observer=None,
) -> ModelAdapter | None:
    resolution = runtime_resolver.resolve(
        profile.provider_id,
        model_id=profile.default_model or None,
        base_url=profile.base_url,
    )
    credential_source = PinnedCredentialSource(
        provider_id=profile.provider_id,
        values=credentials,
    )
    context = ModelAdapterBuildContext(
        profile=profile,
        resolution=resolution,
        runtime_resolver=runtime_resolver,
        credential_source=credential_source,
        credentials=credentials,
        adapter_id=adapter_id,
        stream_observer=stream_observer,
    )
    try:
        builder = default_model_adapter_builder_registry().select(context)
    except LookupError:
        return None
    return builder.build(context)
