from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


SCENARIOS_PATH = ROOT / "tests" / "scenarios" / "memory" / "scenarios.yaml"
SCENARIO_DIR = ROOT / "tests" / "scenarios" / "memory"


class MemoryScenarioFixtureTests(unittest.TestCase):
    def test_memory_scenario_manifest_is_stable(self) -> None:
        manifest = json.loads(SCENARIOS_PATH.read_text(encoding="utf-8"))

        self.assertEqual(manifest["track"], "MOD-2")
        self.assertEqual(
            [scenario["id"] for scenario in manifest["scenarios"]],
            [
                "memory.durable-memory-substrate",
                "memory.resume-after-gap",
                "memory.correction-and-deletion",
            ],
        )

    def test_memory_scenario_files_exist(self) -> None:
        manifest = json.loads(SCENARIOS_PATH.read_text(encoding="utf-8"))

        for scenario in manifest["scenarios"]:
            self.assertTrue((SCENARIO_DIR / scenario["file"]).exists(), scenario["file"])

    def test_memory_scenario_assertions_are_explicit(self) -> None:
        manifest = json.loads(SCENARIOS_PATH.read_text(encoding="utf-8"))

        for scenario in manifest["scenarios"]:
            self.assertGreaterEqual(len(scenario["primary_assertions"]), 3)


if __name__ == "__main__":
    unittest.main()
