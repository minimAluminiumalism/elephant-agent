from __future__ import annotations

import unittest

from packages.contracts import RelationshipMemoryRecord
from packages.contracts.runtime import PersonalModelRuntimeState
from packages.state import (
    CompanionSettings,
    build_canonical_profile_state,
    build_loaded_profile_from_state,
    canonical_profile_ids,
    render_user_profile_text,
)
from packages.state.persistence import _relationship_capture_content


class CanonicalPersonalModelRuntimeStateTest(unittest.TestCase):
    def _load_profile(self):
        """Construct a LoadedProfile directly (no profile.json on disk)."""
        runtime_state = PersonalModelRuntimeState(
            profile_id="you",
            display_name="Aeon",
            mode="companion",
            preferences=(
                "tone:steady",
                "verbosity:concise",
                "local-context:agentic-in/elephant",
            ),
        )
        companion = CompanionSettings(
            personality_preset="companion",
            initiative="proactive",
            notes=("recover long arcs", "surface the next move"),
        )
        manifest = {
            "locale": "zh-CN",
            "timezone": "Asia/Shanghai",
        }
        return build_loaded_profile_from_state(
            runtime_state,
            manifest=manifest,
            companion=companion,
            profile_dir="",
            manifest_path=None,
            elephant_identity_text=(
                "Protect continuity, stay exact, and keep the user oriented around "
                "the next useful move."
            ),
            user_profile_text=render_user_profile_text(
                preferred_name="Bit",
                current_work="Building durable agent systems.",
                current_city="Shanghai",
                dream="Build a remembered AI collaborator.",
                boundaries="Prefer directness over fluff.",
                durable_notes=("Carries research context across weeks.",),
            ),
        )

    def test_canonical_profile_ids_are_stable(self) -> None:
        ids = canonical_profile_ids("profile-companion")

        self.assertEqual(ids.elephant_id, "you:elephant")
        self.assertEqual(ids.user_card_id, "you:user-card")
        self.assertEqual(ids.relationship_id, "you:relationship")

    def test_build_canonical_profile_state_separates_user_and_relationship_truth(self) -> None:
        loaded = self._load_profile()
        bundle = build_canonical_profile_state(loaded)

        self.assertEqual(bundle.personal_model_record_bundle.profile.profile_id, "you")
        self.assertEqual(bundle.personal_model_record_bundle.elephant_identity.elephant_id, bundle.elephant_identity.elephant_id)
        self.assertEqual(bundle.personal_model_record_bundle.user_card.user_card_id, bundle.user_card.user_card_id)
        self.assertEqual(
            bundle.personal_model_record_bundle.relationship_memory.relationship_id,
            bundle.relationship_memory.relationship_id,
        )

        self.assertEqual(bundle.elephant_identity.profile_id, "you")
        self.assertEqual(bundle.elephant_identity.display_name, "Aeon")
        self.assertEqual(bundle.elephant_identity.personality_preset, "companion")
        self.assertEqual(bundle.elephant_identity.initiative, "proactive")
        self.assertIn("Protect continuity", bundle.elephant_identity.elephant_identity_text or "")
        self.assertIn("text-first", bundle.elephant_identity.governance_flags)

        self.assertEqual(bundle.user_card.preferred_name, "Bit")
        self.assertEqual(bundle.user_card.locale, "zh-CN")
        self.assertEqual(bundle.user_card.timezone, "Asia/Shanghai")
        self.assertEqual(bundle.user_card.communication_preferences, ("tone:steady", "verbosity:concise"))
        self.assertEqual(bundle.user_card.shared_preferences, ("local-context:agentic-in/elephant",))
        self.assertIn("current_work:Building durable agent systems.", bundle.user_card.biography_fragments)
        self.assertIn("current_city:Shanghai", bundle.user_card.biography_fragments)
        self.assertEqual(bundle.user_card.boundaries, ("Prefer directness over fluff.",))
        self.assertEqual(bundle.user_card.durable_notes, ("Carries research context across weeks.",))

        self.assertEqual(bundle.relationship_memory.elephant_id, bundle.elephant_identity.elephant_id)
        self.assertEqual(bundle.relationship_memory.user_card_id, bundle.user_card.user_card_id)
        self.assertIn("initiative:proactive", bundle.relationship_memory.expectations)
        self.assertIn("recover long arcs", bundle.relationship_memory.continuity_notes)
        self.assertNotIn("current_work:Building durable agent systems.", bundle.relationship_memory.expectations)
        self.assertNotIn("Prefer directness over fluff.", bundle.relationship_memory.continuity_notes)

    def test_relationship_capture_excludes_system_governance_defaults(self) -> None:
        record = RelationshipMemoryRecord(
            relationship_id="you:relationship",
            profile_id="you",
            elephant_id="you:elephant",
            user_card_id="you:user-card",
            interaction_preferences=(
                "text-first",
                "preserve-relationship-timeline",
                "preserve-preferences",
                "preserve-corrections",
                "preserve-emotional-context",
            ),
            expectations=(
                "initiative:gentle",
                "relational_stance:close companion with clear boundaries",
                "personality_label:Companion",
            ),
        )

        self.assertEqual(_relationship_capture_content(record), "")

        with_note = RelationshipMemoryRecord(
            relationship_id="you:relationship",
            profile_id="you",
            elephant_id="you:elephant",
            user_card_id="you:user-card",
            interaction_preferences=record.interaction_preferences,
            expectations=record.expectations,
            continuity_notes=("Check in gently after intense work sessions.",),
        )
        captured = _relationship_capture_content(with_note)
        self.assertIn("Continuity note: Check in gently", captured)
        self.assertNotIn("Interaction preference: text-first", captured)
        self.assertNotIn("Expectation: initiative:gentle", captured)


if __name__ == "__main__":
    unittest.main()
