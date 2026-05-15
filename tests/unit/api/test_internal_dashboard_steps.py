from __future__ import annotations

from datetime import datetime, timezone
import unittest

from apps.api.api_runtime_internal_methods import _dashboard_step_row
from packages.contracts.layers import Step


class InternalDashboardStepRowsTest(unittest.TestCase):
    def test_tool_execute_detail_includes_exact_tool_result(self) -> None:
        step = Step(
            step_id="step:tool",
            loop_id="loop:test",
            episode_id="episode:test",
            state_id="state:test",
            personal_model_id="you",
            phase="acting",
            action="call_tool",
            status="completed",
            sequence=1,
            created_at=datetime.now(timezone.utc),
            summary="tool.diary.list description should not be the result",
            metadata={
                "tool_name": "tool.diary.list",
                "tool_arguments": '{"limit":5}',
                "tool_result": '{"entries":[],"count":0}',
                "execution_id": "exec:tool",
            },
        )

        row = _dashboard_step_row(step, {})

        self.assertEqual(row["event_type"], "tool_execute")
        self.assertEqual(row["content"], '{"entries":[],"count":0}')
        self.assertEqual(row["detail"]["tool_name"], "tool.diary.list")
        self.assertEqual(row["detail"]["tool_arguments"], '{"limit":5}')
        self.assertEqual(row["detail"]["tool_result"], '{"entries":[],"count":0}')


if __name__ == "__main__":
    unittest.main()
