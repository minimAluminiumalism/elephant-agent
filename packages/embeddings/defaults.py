"""Default local Elephant Agent embedding provider assembly."""

from __future__ import annotations

from .runtime import (
    ELEPHANT_EMBED_MODEL_ID,
    ELEPHANT_EMBED_ONLINE_DIMENSIONS,
    ELEPHANT_EMBED_PROVIDER_ID,
    ELEPHANT_EMBED_SOURCE_URL,
    DefaultEmbeddingService,
    InMemoryEmbeddingModelRegistry,
    SentenceTransformerEmbeddingProvider,
)

ELEPHANT_EMBED_PROVIDER_KIND = "local-elephant"
ELEPHANT_EMBED_DEFAULT_DIMENSIONS = 256
OPENAI_COMPATIBLE_EMBED_PROVIDER_ID = "openai-compatible-embed"
OPENAI_COMPATIBLE_EMBED_PROVIDER_KIND = "openai-compatible"
OPENAI_COMPATIBLE_EMBED_PROFILE_ID = "provider-embedding-openai-compatible"
OPENAI_COMPATIBLE_EMBED_SECRET_REFERENCE_ID = "secret-embedding-provider-openai-compatible-active-api-key"
OPENAI_COMPATIBLE_EMBED_DEFAULT_SECRET_ENV_VAR = "OPENAI_API_KEY"


class LocalElephantEmbeddingProvider(SentenceTransformerEmbeddingProvider):
    """Canonical default embedding provider for the reset runtime."""


def default_local_embedding_provider_config(
    *,
    dimensions: int = ELEPHANT_EMBED_DEFAULT_DIMENSIONS,
) -> dict[str, object]:
    if dimensions not in ELEPHANT_EMBED_ONLINE_DIMENSIONS:
        raise ValueError(f"local Elephant Agent embedding dimensions must be one of {ELEPHANT_EMBED_ONLINE_DIMENSIONS}")
    return {
        "profile_id": "",
        "provider_id": ELEPHANT_EMBED_PROVIDER_ID,
        "model_id": ELEPHANT_EMBED_MODEL_ID,
        "dimensions": dimensions,
        "provider_kind": ELEPHANT_EMBED_PROVIDER_KIND,
        "base_url": "",
        "metadata": {"source_url": ELEPHANT_EMBED_SOURCE_URL, "default": "true"},
    }


def build_default_embedding_service() -> DefaultEmbeddingService:
    return DefaultEmbeddingService(
        registry=InMemoryEmbeddingModelRegistry((LocalElephantEmbeddingProvider(),)),
        default_provider_id=ELEPHANT_EMBED_PROVIDER_ID,
    )
