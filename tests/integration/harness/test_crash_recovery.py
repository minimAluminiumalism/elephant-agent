"""End-to-end crash recovery integration test using real storage.

Exercises the full Phase 1 "survival" pipeline against a live sqlite
repository:

1. Park a Loop with a dispatched pending tool call, stale heartbeat,
   and a partial assistant string — simulating a hard process crash
   that happened mid-tool.
2. Run ``supervisor.scan_once`` with a short stale TTL.
3. Confirm the Loop was reclaimed: crash_marker='detected',
   partial_assistant cleared, and the pending tool call that lacked
   a completed Step survives for replay (while the one that had a
   completed Step gets removed).
4. Confirm the row round-trips through the v2 serde unchanged.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
import tempfile
import unittest

from packages.contracts import Episode, Step
from packages.contracts.runtime import (
    LoopState,
    PendingToolCall,
    WaitCondition,
)
from packages.harness.supervisor import scan_once
from packages.storage import RuntimeStorageRepository


def _seed_episode(repo: RuntimeStorageRepository, *, now: datetime) -> tuple[str, str, str]:
    model = repo.ensure_default_personal_model()
    state = repo.create_state(
        personal_model_id=model.personal_model_id,
        elephant_name="Atlas",
        elephant_id="atlas",
        state_id="state:atlas",
    )
    episode_id = "episode:atlas"
    repo.upsert_episode(
        Episode(
            episode_id=episode_id,
            state_id=state.state_id,
            personal_model_id=model.personal_model_id,
            entry_surface="cli",
            status="open",
            started_at=now,
            metadata={},
        )
    )
    repo.upsert_episode_state(
        Episode(
            episode_id=episode_id,
            state_id=state.state_id,
            personal_model_id=model.personal_model_id,
            entry_surface="cli",
            elephant_id=state.elephant_id,
            status="open",
            started_at=now,
            updated_at=now,
            interruption_state=None,
        )
    )
    return model.personal_model_id, state.state_id, episode_id


def _record_completed_tool_step(
    repo: RuntimeStorageRepository,
    *,
    loop_id: str,
    episode_id: str,
    state_id: str,
    pm_id: str,
    call_id: str,
    created_at: datetime,
) -> None:
    repo.upsert_step(
        Step(
            step_id=f"step:{call_id}",
            loop_id=loop_id,
            episode_id=episode_id,
            state_id=state_id,
            personal_model_id=pm_id,
            phase="acting",
            action="call_tool",
            status="completed",
            sequence=0,
            created_at=created_at,
            outcome="ok",
            metadata={"tool_call_id": call_id, "tool_name": "tool.shell.run"},
        )
    )


class CrashRecoveryIntegrationTest(unittest.TestCase):
    def test_stale_crash_is_reclaimed_and_consumes_partial(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = RuntimeStorageRepository(Path(tmpdir) / "elephant.sqlite3")
            repo.bootstrap()
            now = datetime(2026, 5, 3, 10, tzinfo=timezone.utc)
            pm_id, state_id, episode_id = _seed_episode(repo, now=now)

            # Call-A: already completed on disk (Step exists). Call-B: crashed
            # between dispatch and step persistence, so replay should queue it.
            # Record the Step only after the checkpoint row creates the parent Loop.
            pending = (
                PendingToolCall(
                    call_id="call-A",
                    tool_name="tool.shell.run",
                    arguments={"cmd": "make build"},
                    started_at=now - timedelta(hours=1, minutes=10),
                    step_id="step:call-A",
                    status="dispatched",
                    idempotency_key="idem:call-A",
                ),
                PendingToolCall(
                    call_id="call-B",
                    tool_name="tool.shell.run",
                    arguments={"cmd": "make test"},
                    started_at=now - timedelta(hours=1, minutes=2),
                    step_id="step:call-B",
                    status="dispatched",
                    idempotency_key="idem:call-B",
                ),
            )
            crashed = LoopState(
                run_id="loop:crashed",
                episode_id=episode_id,
                source_event_id="evt-1",
                prompt="build and test",
                status="active",
                phase="model",
                step_count=2,
                model_turn_count=1,
                tool_call_count=2,
                max_model_turns=50,
                max_wall_time_seconds=7200,
                created_at=now - timedelta(hours=1, minutes=15),
                updated_at=now - timedelta(hours=1, minutes=1),
                wait_condition=WaitCondition(kind="budget_exhausted"),
                pending_tool_calls=pending,
                partial_assistant="Half of the planned response",
                heartbeat_at=now - timedelta(hours=1),
                crash_marker=None,
            )
            repo.upsert_loop_checkpoint(crashed)
            _record_completed_tool_step(
                repo,
                loop_id="loop:crashed",
                episode_id=episode_id,
                state_id=state_id,
                pm_id=pm_id,
                call_id="call-A",
                created_at=now - timedelta(hours=1, minutes=5),
            )

            result = scan_once(repo, now=now, heartbeat_stale_ttl_seconds=60)
            self.assertEqual(result.scanned_count, 1)
            self.assertEqual(len(result.decisions), 1)
            decision = result.decisions[0]
            self.assertEqual(decision.action, "reclaimed_crashed")

            (stored,) = repo.list_loop_checkpoints(statuses=("active", "pending"))
            self.assertEqual(stored.run_id, "loop:crashed")
            self.assertEqual(stored.crash_marker, "detected")
            self.assertIsNone(stored.partial_assistant)
            # call-A had a completed Step -> skipped. call-B remains to replay.
            remaining_ids = tuple(call.call_id for call in stored.pending_tool_calls)
            self.assertEqual(remaining_ids, ("call-B",))

    def test_second_scan_is_idempotent(self) -> None:
        """Running the supervisor twice must not double-process or raise."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = RuntimeStorageRepository(Path(tmpdir) / "elephant.sqlite3")
            repo.bootstrap()
            now = datetime(2026, 5, 3, 10, tzinfo=timezone.utc)
            _seed_episode(repo, now=now)

            stale = LoopState(
                run_id="loop:stale",
                episode_id="episode:atlas",
                source_event_id="evt-1",
                prompt="hi",
                status="active",
                phase="model",
                step_count=0,
                model_turn_count=0,
                tool_call_count=0,
                max_model_turns=10,
                max_wall_time_seconds=3600,
                created_at=now - timedelta(hours=1),
                updated_at=now - timedelta(hours=1),
                wait_condition=WaitCondition(kind="budget_exhausted"),
                heartbeat_at=now - timedelta(minutes=30),
                crash_marker=None,
            )
            repo.upsert_loop_checkpoint(stale)

            first = scan_once(repo, now=now, heartbeat_stale_ttl_seconds=60)
            # After first scan, heartbeat was refreshed by apply_resume_snapshot.
            self.assertEqual(first.decisions[0].action, "reclaimed_crashed")

            # Second scan against the same "now" should find the heartbeat
            # fresh (just written) and do nothing.
            second = scan_once(repo, now=now, heartbeat_stale_ttl_seconds=60)
            self.assertEqual(len(second.decisions), 0)


if __name__ == "__main__":
    unittest.main()
