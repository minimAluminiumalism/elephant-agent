from __future__ import annotations

from datetime import datetime
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from packages.contracts import (
    ArtifactRecord,
    ElephantIdentityRecord,
    EvidenceRecordBundle,
    MemoryRecord,
    ProcedureLibrary,
    ProcedureRecord,
    ProcedureStep,
    PersonalModelRecordBundle,
    RelationshipMemoryRecord,
    UserCardRecord,
)
from packages.contracts.runtime import (
    PersonalModelRuntimeState,
)


class CanonicalBundleContractsTest(unittest.TestCase):
    def test_personal_model_record_bundle_requires_consistent_owner_references(self) -> None:
        profile = PersonalModelRuntimeState(profile_id="profile-1", display_name="Elephant Agent", mode="companion")
        elephant_identity = ElephantIdentityRecord(
            elephant_id="profile-1:elephant",
            profile_id="profile-1",
            display_name="Elephant Agent",
            identity_mode="companion",
            personality_preset="companion",
            initiative="proactive",
            relational_stance="steady",
            working_style_contract="direct",
        )
        user_card = UserCardRecord(user_card_id="profile-1:user-card", profile_id="profile-1")
        relationship = RelationshipMemoryRecord(
            relationship_id="profile-1:relationship",
            profile_id="profile-1",
            elephant_id=elephant_identity.elephant_id,
            user_card_id=user_card.user_card_id,
        )

        bundle = PersonalModelRecordBundle(
            profile=profile,
            elephant_identity=elephant_identity,
            user_card=user_card,
            relationship_memory=relationship,
        )

        self.assertEqual(bundle.profile.profile_id, "profile-1")
        self.assertEqual(bundle.relationship_memory.elephant_id, bundle.elephant_identity.elephant_id)

        with self.assertRaises(ValueError):
            PersonalModelRecordBundle(
                profile=profile,
                elephant_identity=elephant_identity,
                user_card=user_card,
                relationship_memory=RelationshipMemoryRecord(
                    relationship_id="profile-1:relationship",
                    profile_id="profile-1",
                    elephant_id="other-elephant",
                    user_card_id=user_card.user_card_id,
                ),
            )

    def test_evidence_record_bundle_rejects_cross_session_records(self) -> None:
        bundle = EvidenceRecordBundle(
            episode_id="session-1",
            memories=(
                MemoryRecord(
                    memory_id="memory-1",
                    episode_id="session-1",
                    kind="fact",
                    content="User prefers concise updates.",
                    created_at=datetime(2026, 1, 1),
                ),
            ),
            artifacts=(
                ArtifactRecord(
                    artifact_id="artifact-1",
                    episode_id="session-1",
                    kind="doc",
                    name="notes.md",
                    uri="file:///notes.md",
                ),
            ),
        )

        self.assertEqual(bundle.episode_id, "session-1")
        self.assertEqual(bundle.memories[0].memory_id, "memory-1")

        with self.assertRaises(ValueError):
            EvidenceRecordBundle(
                episode_id="session-1",
                memories=(
                    MemoryRecord(
                        memory_id="memory-1",
                        episode_id="session-2",
                        kind="fact",
                        content="Wrong session.",
                    ),
                ),
            )

    def test_procedure_library_requires_unique_procedures_and_steps(self) -> None:
        library = ProcedureLibrary(
            profile_id="profile-1",
            procedures=(
                ProcedureRecord(
                    procedure_id="procedure-1",
                    title="Recover activity state",
                    summary="Rebuild the user's active thread from durable evidence.",
                    status="draft",
                    steps=(
                        ProcedureStep(
                            step_id="step-1",
                            title="Load evidence",
                            instruction="Load recent durable evidence for the active work thread.",
                        ),
                    ),
                ),
            ),
        )

        self.assertEqual(library.profile_id, "profile-1")
        self.assertEqual(library.procedures[0].steps[0].step_id, "step-1")

        with self.assertRaises(ValueError):
            ProcedureRecord(
                procedure_id="procedure-2",
                title="Bad procedure",
                summary="Contains duplicate steps.",
                status="draft",
                steps=(
                    ProcedureStep(step_id="step-1", title="One", instruction="Do one thing."),
                    ProcedureStep(step_id="step-1", title="Two", instruction="Do two things."),
                ),
            )

        with self.assertRaises(ValueError):
            ProcedureLibrary(
                profile_id="profile-1",
                procedures=(
                    ProcedureRecord(
                        procedure_id="procedure-1",
                        title="One",
                        summary="First.",
                        status="draft",
                    ),
                    ProcedureRecord(
                        procedure_id="procedure-1",
                        title="Two",
                        summary="Second.",
                        status="draft",
                    ),
                ),
            )


if __name__ == "__main__":
    unittest.main()
