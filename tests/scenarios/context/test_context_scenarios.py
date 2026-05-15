from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


SCENARIOS_PATH = Path(__file__).with_name("scenarios.yaml")


class ContextScenarioFixturesTest(unittest.TestCase):
    def test_context_scenarios_index_is_stable(self) -> None:
        payload = json.loads(SCENARIOS_PATH.read_text(encoding="utf-8"))
        self.assertEqual(payload["track"], "CSR-3")
        self.assertEqual(
            [scenario["id"] for scenario in payload["scenarios"]],
            [
                "context.overflow-recovery",
                "context.continuity-recovery",
                "context.current-work-linked-compaction",
                "context.session-frame-request-refresh",
                "context.mixed-compression-replay",
            ],
        )
        for scenario in payload["scenarios"]:
            self.assertTrue((SCENARIOS_PATH.with_name(scenario["file"])).exists(), scenario["file"])

    def test_context_readme_mentions_overflow_recovery_and_replay(self) -> None:
        readme = SCENARIOS_PATH.with_name("README.md").read_text(encoding="utf-8")
        self.assertIn("overflow", readme)
        self.assertIn("recovery", readme)
        self.assertIn("replay", readme)

    def test_context_scenarios_mention_source_trace(self) -> None:
        for scenario_file in (
            "continuity-recovery.md",
            "overflow-recovery.md",
            "current-work-linked-compaction.md",
            "mixed-compression-replay.md",
        ):
            body = SCENARIOS_PATH.with_name(scenario_file).read_text(encoding="utf-8")
            self.assertIn("source trace", body.lower(), scenario_file)


if __name__ == "__main__":
    unittest.main()
