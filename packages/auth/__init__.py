"""Credential resolution and secret-reference primitives."""

from __future__ import annotations

from .inventory import AUTH_SURFACES
from .runtime import (
    AuthProfile,
    AuthProfileStore,
    CredentialBundle,
    CredentialResolver,
    EncryptedSecretValue,
    InMemoryAuthProfileStore,
    InMemorySecretStore,
    LocalEncryptedSecretCipher,
    PersistentAuthProfileStore,
    PreviewAuthProviderCapability,
    ProfileCredentialResolver,
    ProviderAuthState,
    ProviderCatalog,
    ProviderManifest,
    ProviderProfileFactory,
    ProviderProfileInput,
    profile_from_input,
    SecretReference,
    SecretValueResolution,
    SecretStore,
)
from .discovery import (
    CredentialDiscoveryProvider,
    EncryptedRepositorySecretStore,
    EnvironmentSecretStore,
    InMemoryCredentialDiscoveryRegistry,
    default_credential_discovery_registry,
)

__all__ = [
    "AUTH_SURFACES",
    "AuthProfile",
    "AuthProfileStore",
    "CredentialBundle",
    "CredentialDiscoveryProvider",
    "CredentialResolver",
    "EncryptedRepositorySecretStore",
    "EncryptedSecretValue",
    "EnvironmentSecretStore",
    "InMemoryAuthProfileStore",
    "InMemoryCredentialDiscoveryRegistry",
    "InMemorySecretStore",
    "LocalEncryptedSecretCipher",
    "PersistentAuthProfileStore",
    "PreviewAuthProviderCapability",
    "ProfileCredentialResolver",
    "ProviderCatalog",
    "ProviderManifest",
    "ProviderProfileFactory",
    "ProviderProfileInput",
    "ProviderAuthState",
    "SecretReference",
    "SecretStore",
    "SecretValueResolution",
    "default_credential_discovery_registry",
    "profile_from_input",
]
