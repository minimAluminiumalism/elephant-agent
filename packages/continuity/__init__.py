"""Continuity projection services and canonical continuity helpers."""

from .projection import ContinuityProjection, ContinuityProjectionService
from .runtime import (
    RelationshipPolicy,
    apply_episode_continuity_state,
    build_episode_continuity_state,
    build_relationship_policy,
    normalize_interruption_state,
)

__all__ = [
    "ContinuityProjection",
    "ContinuityProjectionService",
    "RelationshipPolicy",
    "apply_episode_continuity_state",
    "build_episode_continuity_state",
    "build_relationship_policy",
    "normalize_interruption_state",
]
