"""Continuity projection services and canonical continuity helpers."""

from .projection import ContinuityProjection, ContinuityProjectionService
from .runtime import (
    RelationshipMemoryPolicy,
    apply_episode_continuity_state,
    build_episode_continuity_state,
    build_relationship_memory_policy,
    normalize_interruption_state,
)

__all__ = [
    "ContinuityProjection",
    "ContinuityProjectionService",
    "RelationshipMemoryPolicy",
    "apply_episode_continuity_state",
    "build_episode_continuity_state",
    "build_relationship_memory_policy",
    "normalize_interruption_state",
]
