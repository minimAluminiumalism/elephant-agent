from __future__ import annotations

from pathlib import Path
import json
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
SCENARIOS_PATH = Path(__file__).with_name("scenarios.yaml")


class CompanionScenarioFixturesTest(unittest.TestCase):
    def test_companion_scenarios_index_is_stable(self) -> None:
        payload = json.loads(SCENARIOS_PATH.read_text(encoding="utf-8"))
        self.assertEqual(payload["track"], "CMP-1")
        self.assertEqual(
            [scenario["id"] for scenario in payload["scenarios"]],
            ["companion.text-first-continuity", "companion.inspectable-persona-state"],
        )
        for scenario in payload["scenarios"]:
            self.assertTrue((SCENARIOS_PATH.with_name(scenario["file"])).exists(), scenario["file"])

    def test_governance_state_exposes_text_first_persona_state(self) -> None:
        from packages.continuity import build_relationship_policy
        from packages.state import ProfileLoader, build_companion_governance_state, build_loaded_profile_from_state

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            profile_dir = root / "profile"
            profile_dir.mkdir()
            (profile_dir / "profile.json").write_text(
                json.dumps(
                    {
                        "profile_id": "profile-companion",
                        "display_name": "Elephant Agent",
                        "mode": "companion",
                        "companion": {
                            "text_first": True,
                            "personality": ["steady", "present", "grounded"],
                            "initiative": "gentle",
                            "preserve_relationship_timeline": True,
                            "preserve_preferences": True,
                            "preserve_corrections": True,
                            "preserve_emotional_context": True,
                            "notes": ["text-first baseline"],
                        },
                        "preferences": ["tone:steady", "verbosity:concise"],
                        "enabled_capabilities": ["preview.cli"],
                    }
                ),
                encoding="utf-8",
            )
            loaded_source = ProfileLoader(profile_dir).load()
            loaded = build_loaded_profile_from_state(
                loaded_source.state,
                manifest=loaded_source.manifest,
                companion=loaded_source.companion,
                profile_dir=loaded_source.profile_dir,
                manifest_path=loaded_source.manifest_path,
                elephant_identity_text="Steady, grounded, and direct.",
            )
            governance = build_companion_governance_state(loaded)
            relationship_policy = build_relationship_policy(
                loaded.state.mode,
                text_first=loaded.companion.text_first if loaded.companion is not None else True,
                preserve_relationship_timeline=(
                    loaded.companion.preserve_relationship_timeline if loaded.companion is not None else True
                ),
                preserve_preferences=loaded.companion.preserve_preferences if loaded.companion is not None else True,
                preserve_corrections=loaded.companion.preserve_corrections if loaded.companion is not None else True,
                preserve_emotional_context=(
                    loaded.companion.preserve_emotional_context if loaded.companion is not None else True
                ),
            )

        self.assertEqual(governance.identity.display_name, "Elephant Agent")
        self.assertEqual(governance.identity.mode, "companion")
        self.assertIn("state remains inspectable", governance.identity.governance_summary)
        self.assertEqual(governance.identity.personality_traits, ("steady", "present", "grounded"))
        self.assertEqual(governance.identity.elephant_identity_text, "Steady, grounded, and direct.")
        self.assertTrue(relationship_policy.text_first)
        self.assertIn("companion text-first continuity", relationship_policy.summary())

    def test_companion_governance_path_distinguishes_defaults_from_onboarded_identity(self) -> None:
        from packages.state import (
            ProfileLoader,
            build_companion_governance_state,
            build_loaded_profile_from_state,
            render_user_profile_text,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)

            baseline_dir = root / "baseline"
            baseline_dir.mkdir()
            (baseline_dir / "profile.json").write_text(
                json.dumps(
                    {
                        "profile_id": "profile-companion",
                        "mode": "companion",
                    }
                ),
                encoding="utf-8",
            )
            baseline = build_companion_governance_state(ProfileLoader(baseline_dir).load())

            onboarded_dir = root / "onboarded"
            onboarded_dir.mkdir()
            (onboarded_dir / "profile.json").write_text(
                json.dumps(
                    {
                        "profile_id": "profile-companion",
                        "display_name": "Samantha",
                        "mode": "companion",
                        "companion": {
                            "personality_preset": "companion",
                            "initiative": "proactive",
                            "notes": ["check in after long pauses"],
                        },
                    }
                ),
                encoding="utf-8",
            )
            onboarded_source = ProfileLoader(onboarded_dir).load()
            onboarded = build_companion_governance_state(
                build_loaded_profile_from_state(
                    onboarded_source.state,
                    manifest=onboarded_source.manifest,
                    companion=onboarded_source.companion,
                    profile_dir=onboarded_source.profile_dir,
                    manifest_path=onboarded_source.manifest_path,
                    elephant_identity_text="Stay steady, direct, and durable.",
                    user_profile_text=render_user_profile_text(
                        preferred_name="Bit",
                        current_work="Building durable agent systems.",
                    ),
                )
            )

        self.assertTrue(baseline.onboarding.ready)
        self.assertEqual(baseline.onboarding.missing_fields, ())
        self.assertIn("normal turns", baseline.onboarding.summary)
        self.assertTrue(onboarded.onboarding.ready)
        self.assertEqual(onboarded.onboarding.status, "ready")
        self.assertEqual(onboarded.identity.display_name, "Samantha")
        self.assertEqual(onboarded.identity.personality_preset, "companion")
        self.assertEqual(onboarded.identity.initiative, "proactive")
        self.assertIn("normal turns", onboarded.onboarding.summary)

    def test_relationship_policy_hook_matches_companion_state(self) -> None:
        from packages.continuity import build_relationship_policy
        from packages.state import ProfileLoader

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            profile_dir = root / "profile"
            profile_dir.mkdir()
            (profile_dir / "profile.json").write_text(
                json.dumps(
                    {
                        "profile_id": "profile-companion",
                        "display_name": "Elephant Agent",
                        "mode": "companion",
                        "companion": {
                            "text_first": True,
                            "personality": ["steady", "present"],
                        },
                    }
                ),
                encoding="utf-8",
            )

            loaded = ProfileLoader(profile_dir).load()
            policy = build_relationship_policy(
                loaded.state.mode,
                text_first=loaded.companion.text_first if loaded.companion is not None else True,
                preserve_relationship_timeline=(
                    loaded.companion.preserve_relationship_timeline if loaded.companion is not None else True
                ),
                preserve_preferences=loaded.companion.preserve_preferences if loaded.companion is not None else True,
                preserve_corrections=loaded.companion.preserve_corrections if loaded.companion is not None else True,
                preserve_emotional_context=(
                    loaded.companion.preserve_emotional_context if loaded.companion is not None else True
                ),
            )

        self.assertTrue(policy.text_first)
        self.assertTrue(policy.allows("relationship"))
        self.assertFalse(policy.allows("voice"))
        self.assertIn("text-first", policy.summary())

    def test_profile_writers_can_update_identity_and_elephant_state(self) -> None:
        from apps.cli.runtime import CliRuntime
        from packages.state import (
            build_companion_governance_state,
            render_user_profile_text,
            write_profile_manifest,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            profile_dir = root / "profile"
            profile_dir.mkdir()
            (profile_dir / "profile.json").write_text(
                json.dumps(
                    {
                        "profile_id": "profile-companion",
                        "display_name": "Elephant Agent",
                        "mode": "companion",
                        "companion": {
                            "text_first": True,
                            "personality": ["steady", "present"],
                            "initiative": "gentle",
                        },
                    }
                ),
                encoding="utf-8",
            )
            write_profile_manifest(
                profile_dir,
                {
                    "profile_id": "profile-companion",
                    "display_name": "Samantha",
                    "mode": "companion",
                    "companion": {
                        "text_first": True,
                        "personality": ["steady", "grounded"],
                        "initiative": "proactive",
                        "notes": ["check in after long pauses"],
                    },
                },
            )
            runtime = CliRuntime.create(state_dir=root / "state")
            runtime.update_identity_state(
                profile_id="profile-companion",
                elephant_identity_text="Stay steady, direct, and durable.",
            )
            runtime.update_user_state(
                profile_id="profile-companion",
                text=render_user_profile_text(
                    preferred_name="Bit",
                    current_work="Building durable agent systems.",
                ),
            )
            governance = build_companion_governance_state(runtime.inspect_profile("profile-companion"))

        self.assertEqual(governance.identity.display_name, "Samantha")
        self.assertEqual(governance.identity.initiative, "proactive")
        self.assertEqual(governance.identity.personality_traits, ("steady", "grounded"))
        self.assertTrue(governance.onboarding.ready)

    def test_companion_turn_reconciliation_does_not_mutate_profile_without_management_tools(self) -> None:
        from apps.cli.runtime import CliRuntime

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            profile_dir = root / "profile"
            state_dir = root / "state"
            profile_dir.mkdir()
            (profile_dir / "profile.json").write_text(
                json.dumps(
                    {
                        "profile_id": "profile-companion",
                        "display_name": "Elephant Agent",
                        "mode": "companion",
                        "companion": {"initiative": "gentle"},
                    }
                ),
                encoding="utf-8",
            )
            runtime = CliRuntime.create(state_dir=state_dir)
            session = runtime.start()

            outcome = runtime.explain_next_step(
                session_id=session.session_id,
                prompt="Call me Bit. I'm building durable agent systems. Please keep replies concise and grounded for future turns.",
            )
            runtime.explain_next_step(
                session_id=session.session_id,
                prompt="What should we do next?",
            )
            user = runtime.inspect_user(session_id=session.session_id)
            relationship = runtime.inspect_relationship(session_id=session.session_id)

        self.assertIsNone(user.preferred_name)
        self.assertEqual(user.communication_preferences, ())
        self.assertEqual(user.biography_fragments, ())
        self.assertEqual(relationship.continuity_notes, ())
        self.assertEqual(outcome.state.active_task, "Call me Bit. I'm building durable agent systems. Please keep replies concise and grounded for future turns.")


if __name__ == "__main__":
    unittest.main()
