"""Contract inventory tests for the v5 personal-model shape.

This test pins the public contract surface as emitted by
``packages.contracts.__all__``: the four‑lens Observation / Fact /
OpenQuestion trio plus the core system-layer records.  Anything that
referred to the old 6-component taxonomy (CoreMemory, BigFiveTraitSignal,
PersonalityStyleModel, PersonalKnowledge, EpisodicIndex, ProceduralMemory,
RelationshipMemory) has been removed per the Observation/Fact redesign
and should no longer be reachable.
"""

from __future__ import annotations

from dataclasses import is_dataclass
from datetime import datetime, timezone
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import packages.contracts as contracts
from packages.capabilities import CAPABILITY_SURFACES
from packages.capabilities.runtime import (
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
from packages.contracts import (
    ActiveProviderSelection,
    CONTRACT_SURFACES,
    Episode,
    Fact,
    GenerationProviderConfig,
    Grounding,
    Loop,
    MemoryEntry,
    Observation,
    OpenQuestion,
    PersonalModel,
    Record,
    ReflectionProposal,
    SemanticIndexEntry,
    State,
    Step,
)


REMOVED_PUBLIC_CONTRACT_SURFACES = (
    "BigFiveTraitSignal",
    "PersonalityStyleModel",
    "CoreMemory",
    "PersonalKnowledge",
    "EpisodicIndex",
    "ProceduralMemory",
    "RelationshipMemory",
    "BigFiveProfile",
    "PersonalityProfile",
    "BIG_FIVE_AXES",
    "big_five_to_mapping",
    "blend_big_five",
    "parse_big_five_mapping",
)


class ContractInventoryTest(unittest.TestCase):
    def test_contract_inventory_matches_current_design(self) -> None:
        # The four-lens design (ADR-0001/0003) collapses the old 6-component
        # taxonomy into Observation / Fact.  OpenQuestion carries the
        # Curiosity subsystem's prompts.  Everything else is the core
        # system-layer triple.
        self.assertEqual(
            CONTRACT_SURFACES,
            (
                "PersonalModel",
                "State",
                "Episode",
                "Loop",
                "Step",
                "Record",
                "Grounding",
                "MemoryEntry",
                "ReflectionProposal",
                "SemanticIndexEntry",
                "Observation",
                "Fact",
                "OpenQuestion",
                "GenerationProviderConfig",
                "ActiveProviderSelection",
            ),
        )

    def test_contract_root_all_includes_new_types(self) -> None:
        self.assertIn("Observation", contracts.__all__)
        self.assertIn("Fact", contracts.__all__)
        self.assertIn("OpenQuestion", contracts.__all__)
        self.assertIn("ALLOWED_LENSES", contracts.__all__)
        self.assertIn("ALLOWED_OBSERVATION_SOURCES", contracts.__all__)
        self.assertIn("ALLOWED_FACT_SOURCES", contracts.__all__)

    def test_removed_public_surfaces_are_not_importable(self) -> None:
        for surface in REMOVED_PUBLIC_CONTRACT_SURFACES:
            with self.subTest(surface=surface):
                self.assertNotIn(surface, CONTRACT_SURFACES)
                self.assertNotIn(surface, contracts.__all__)
                self.assertFalse(hasattr(contracts, surface))

    def test_capability_inventory_is_stable(self) -> None:
        self.assertEqual(
            CAPABILITY_SURFACES,
            (
                "CapabilityDescriptor",
                "CapabilityHealth",
                "CapabilityRegistry",
                "MemoryCapability",
                "ContextCapability",
                "ModelProviderCapability",
                "AuthProviderCapability",
                "ToolCapability",
                "SkillCapability",
                "DeliveryAdapterCapability",
                "StorageBackendCapability",
                "TelemetrySinkCapability",
            ),
        )

    def test_contract_shapes_are_dataclasses(self) -> None:
        for contract_type in (
            PersonalModel,
            State,
            Episode,
            Loop,
            Step,
            Record,
            Grounding,
            MemoryEntry,
            ReflectionProposal,
            SemanticIndexEntry,
            Observation,
            Fact,
            OpenQuestion,
            GenerationProviderConfig,
            ActiveProviderSelection,
        ):
            self.assertTrue(is_dataclass(contract_type), contract_type.__name__)

    def test_capability_ports_expose_registry_and_health_contracts(self) -> None:
        descriptor = CapabilityDescriptor(
            capability_id="model.openai",
            kind="model_provider",
            version="1.0.0",
        )
        health = CapabilityHealth(status="healthy", checked_at=datetime(2026, 1, 1))

        self.assertEqual(descriptor.capability_id, "model.openai")
        self.assertEqual(health.status, "healthy")
        self.assertTrue(issubclass(CapabilityRegistry, object))
        for protocol in (
            MemoryCapability,
            ContextCapability,
            ModelProviderCapability,
            AuthProviderCapability,
            ToolCapability,
            SkillCapability,
            DeliveryAdapterCapability,
            StorageBackendCapability,
            TelemetrySinkCapability,
        ):
            self.assertTrue(hasattr(protocol, "__dict__"), protocol.__name__)


class ObservationFactOpenQuestionShapeTest(unittest.TestCase):
    """Smoke-tests for the v5 Observation / Fact / OpenQuestion trio."""

    def test_observation_records_raw_signal_with_lens_and_source(self) -> None:
        now = datetime.now(timezone.utc)
        observation = Observation(
            observation_id="obs-1",
            personal_model_id="pm-1",
            text="Prefers short, direct updates",
            confidence=0.6,
            episode_id="episode-1",
            last_seen_at=now,
            source="chat_llm_note",
            lens="identity",
            sub_lens="feedback_preference",
        )
        self.assertEqual(observation.lens, "identity")
        self.assertEqual(observation.sub_lens, "feedback_preference")
        self.assertEqual(observation.source, "chat_llm_note")
        self.assertAlmostEqual(observation.confidence, 0.6)

    def test_fact_is_active_and_confident_by_default(self) -> None:
        now = datetime.now(timezone.utc)
        fact = Fact(
            fact_id="fact-1",
            personal_model_id="pm-1",
            lens="journey",
            text="Plans carefully before shipping",
            confidence=0.8,
            committed_at=now,
            source="pm_agent_promote",
        )
        self.assertEqual(fact.status, "active")
        self.assertGreaterEqual(fact.confidence, 0.6)

    def test_open_question_defaults_to_open_status(self) -> None:
        now = datetime.now(timezone.utc)
        question = OpenQuestion(
            question_id="oq-1",
            personal_model_id="pm-1",
            lens="pulse",
            sub_lens="current_chapter",
            text="What are you working on these days?",
            rationale="coverage_gap: no facts yet under chapter.current_chapter",
            priority=0.8,
            sensitivity="low",
            source="coverage_gap",
            created_at=now,
        )
        self.assertEqual(question.status, "open")
        self.assertEqual(question.asked_count, 0)


if __name__ == "__main__":
    unittest.main()
