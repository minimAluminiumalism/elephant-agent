"""Provider auth-state repository methods - legacy no-ops.

Provider auth state is now derived from auth-profiles.json at runtime via
repository_scope_methods; records is not part of the clean storage schema.
"""

from __future__ import annotations

from packages.auth.runtime import ProviderAuthState


def upsert_provider_auth_state(self, state: ProviderAuthState) -> None:
    pass


def load_provider_auth_state(self, provider_id: str) -> ProviderAuthState | None:
    return None


def list_provider_auth_states(self) -> tuple[ProviderAuthState, ...]:
    return ()


__all__ = [
    "list_provider_auth_states",
    "load_provider_auth_state",
    "upsert_provider_auth_state",
]
