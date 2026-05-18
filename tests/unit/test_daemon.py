"""Unit tests for the unified Elephant daemon public API and task guard."""

from __future__ import annotations

import asyncio
import json
import os
import signal
import sys
import time
import warnings
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest


# ── daemon_command public API tests ──────────────────────────────


class TestDaemonPidPath:
    """Tests for daemon_pid_path / daemon_record_path."""

    def test_pid_path(self, tmp_path: Path) -> None:
        from apps.daemon_command import daemon_pid_path

        result = daemon_pid_path(tmp_path)
        assert result == tmp_path / "daemon.pid"

    def test_record_path(self, tmp_path: Path) -> None:
        from apps.daemon_command import daemon_record_path

        result = daemon_record_path(tmp_path)
        assert result == tmp_path / "daemon.runtime.json"


class TestDaemonIsRunning:
    """Tests for daemon_is_running."""

    def test_no_pid_file(self, tmp_path: Path) -> None:
        from apps.daemon_command import daemon_is_running

        assert daemon_is_running(tmp_path) is False

    def test_stale_pid_file(self, tmp_path: Path) -> None:
        from apps.daemon_command import daemon_is_running

        pid_path = tmp_path / "daemon.pid"
        pid_path.write_text("99999999\n", encoding="utf-8")
        assert daemon_is_running(tmp_path) is False

    def test_current_pid(self, tmp_path: Path) -> None:
        from apps.daemon_command import daemon_is_running

        pid_path = tmp_path / "daemon.pid"
        pid_path.write_text(f"{os.getpid()}\n", encoding="utf-8")
        assert daemon_is_running(tmp_path) is True


class TestStartDaemonDetached:
    """Tests for start_daemon_detached."""

    def test_already_running(self, tmp_path: Path) -> None:
        from apps.daemon_command import start_daemon_detached

        # Write current pid to simulate a running daemon
        pid_path = tmp_path / "daemon.pid"
        pid_path.write_text(f"{os.getpid()}\n", encoding="utf-8")

        result = start_daemon_detached(tmp_path, tmp_path)
        assert result == 1  # Should refuse to start

    def test_start_and_cleanup(self, tmp_path: Path) -> None:
        """Verify that start_daemon_detached writes PID and record files."""
        from apps.daemon_command import start_daemon_detached

        # Patch subprocess.Popen to simulate a successful daemon start
        with patch("apps.daemon_command.subprocess.Popen") as mock_popen:
            mock_process = mock_popen.return_value
            mock_process.pid = 12345
            mock_process.poll.return_value = None  # Still running

            result = start_daemon_detached(tmp_path, tmp_path)

            assert result == 0
            pid_path = tmp_path / "daemon.pid"
            assert pid_path.exists()
            assert "12345" in pid_path.read_text()

            record_path = tmp_path / "daemon.runtime.json"
            assert record_path.exists()
            record = json.loads(record_path.read_text())
            assert record["status"] == "running"
            assert record["pid"] == 12345

    def test_start_suppresses_expected_detached_process_warning(self, tmp_path: Path) -> None:
        """Detached daemon ownership moves to pidfile state, not the local Popen wrapper."""
        from apps.daemon_command import start_daemon_detached

        class WarningProcess:
            pid = 12346

            def poll(self) -> None:
                return None

            def __del__(self) -> None:
                warnings.warn(
                    "subprocess 12346 is still running",
                    ResourceWarning,
                    stacklevel=2,
                )

        with patch("apps.daemon_command.subprocess.Popen", side_effect=lambda *_args, **_kwargs: WarningProcess()):
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always", ResourceWarning)
                result = start_daemon_detached(tmp_path, tmp_path)

        assert result == 0
        assert not [
            warning
            for warning in caught
            if warning.category is ResourceWarning
            and "subprocess 12346 is still running" in str(warning.message)
        ]


class TestStopDaemon:
    """Tests for stop_daemon."""

    def test_not_running(self, tmp_path: Path) -> None:
        from apps.daemon_command import stop_daemon

        result = stop_daemon(tmp_path)
        assert result == 0

    def test_stop_with_current_pid(self, tmp_path: Path) -> None:
        """Stopping the current process should not actually kill it (will fail with PermissionError or succeed)."""
        from apps.daemon_command import stop_daemon

        # Use our own PID — the stop command will try SIGTERM but we handle it
        pid_path = tmp_path / "daemon.pid"
        pid_path.write_text(f"{os.getpid()}\n", encoding="utf-8")
        record_path = tmp_path / "daemon.runtime.json"
        record_path.write_text(json.dumps({"status": "running", "pid": os.getpid()}))

        # This will send SIGTERM to our own process; Python's default handler
        # may or may not raise. We patch os.kill to avoid actually killing ourselves.
        with patch("apps.daemon_command.os.kill") as mock_kill:
            mock_kill.side_effect = ProcessLookupError
            result = stop_daemon(tmp_path)
            assert result == 0


# ── daemon task guard tests ──────────────────────────────────────


class TestDaemonTaskGuard:
    """Tests for _daemon_task_guard."""

    def test_normal_completion(self) -> None:
        from apps.daemon import DaemonServiceStatus, _daemon_task_guard

        statuses: dict[str, DaemonServiceStatus] = {
            "test": DaemonServiceStatus(name="test", status="running")
        }

        async def _inner():
            pass  # Complete normally

        async def _run():
            task = asyncio.create_task(_inner())
            await _daemon_task_guard(task, "test", statuses)

        asyncio.run(_run())
        assert statuses["test"].status == "running"  # No change on success

    def test_exception_updates_status(self) -> None:
        from apps.daemon import DaemonServiceStatus, _daemon_task_guard

        statuses: dict[str, DaemonServiceStatus] = {
            "test": DaemonServiceStatus(name="test", status="running")
        }

        async def _inner():
            raise RuntimeError("boom")

        async def _run():
            task = asyncio.create_task(_inner())
            await _daemon_task_guard(task, "test", statuses)

        asyncio.run(_run())
        assert statuses["test"].status == "failed"
        assert "boom" in (statuses["test"].last_error or "")

    def test_cancellation_cancels_inner(self) -> None:
        """When the guard is cancelled, the inner task should also be cancelled."""
        from apps.daemon import DaemonServiceStatus, _daemon_task_guard

        statuses: dict[str, DaemonServiceStatus] = {
            "test": DaemonServiceStatus(name="test", status="running")
        }
        inner_cancelled = False

        async def _inner():
            nonlocal inner_cancelled
            try:
                await asyncio.sleep(100)
            except asyncio.CancelledError:
                inner_cancelled = True
                raise

        async def _run():
            task = asyncio.create_task(_inner())
            guard = asyncio.create_task(
                _daemon_task_guard(task, "test", statuses),
                name="guard:test",
            )
            # Give the inner task time to start
            await asyncio.sleep(0.05)
            # Cancel the guard (simulating shutdown)
            guard.cancel()
            try:
                await guard
            except asyncio.CancelledError:
                pass

        asyncio.run(_run())
        assert inner_cancelled, "Inner task should have been cancelled when guard was cancelled"


class TestServiceDaemonStartup:
    """Tests for daemon service startup wiring."""

    def test_gateway_app_start_disables_standalone_learning_worker(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        from apps.daemon import ServiceDaemon
        import apps.gateway.runtime_impl as gateway_runtime

        captured: dict[str, object] = {}

        def fake_build_gateway_app(**kwargs: object) -> tuple[object, object, object]:
            captured.update(kwargs)
            return SimpleNamespace(profile_id="you"), object(), object()

        monkeypatch.setattr(gateway_runtime, "build_gateway_app", fake_build_gateway_app)

        daemon = ServiceDaemon(state_dir=tmp_path, cli_state_dir=tmp_path)
        asyncio.run(daemon._start_gateway_app())

        assert captured["state_dir"] == str(tmp_path)
        assert captured["start_learning_worker"] is False


# ── daemon_tasks import structure test ───────────────────────────


class TestDaemonTasksImports:
    """Verify daemon_tasks has clean imports at the top."""

    def test_datetime_at_top(self) -> None:
        import ast

        source = Path("apps/daemon_tasks.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        # Find all ImportFrom nodes at module level
        datetime_imports = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
            and node.module == "datetime"
            and any(alias.name in ("UTC", "datetime") for alias in node.names)
        ]
        assert len(datetime_imports) >= 1, "datetime import should exist at module level"
        # Verify none at the bottom (after function defs)
        last_func_line = max(
            node.lineno for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)
        )
        for imp in datetime_imports:
            assert imp.lineno < last_func_line, (
                f"datetime import at line {imp.lineno} should be at the top, "
                f"not after function definitions (last func at line {last_func_line})"
            )


class TestLearningWorkerLoop:
    """Tests for daemon learning worker event-loop behavior."""

    def test_claimed_learning_job_runs_off_event_loop(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        from apps import daemon_tasks

        class FakeRepository:
            def __init__(self) -> None:
                self.claimed = False

            def bootstrap(self) -> None:
                pass

            def claim_learning_job(self, *, worker_id: str) -> object | None:
                if self.claimed:
                    return None
                self.claimed = True
                return SimpleNamespace(job_id="job-1", progress_stage="queued", attempt_count=1)

            def fail_learning_job(self, *_args: object, **_kwargs: object) -> None:
                pytest.fail("learning job should not fail")

        repository = FakeRepository()
        running = True

        def fake_repository_factory(_database_path: Path) -> FakeRepository:
            return repository

        def fake_write_record(*_args: object, **_kwargs: object) -> dict[str, object]:
            return {}

        def fake_run_claimed_job(_state_dir: Path, _job_id: str, _worker_id: str) -> None:
            nonlocal running
            time.sleep(0.2)
            running = False

        monkeypatch.setattr(daemon_tasks, "RuntimeStorageRepository", fake_repository_factory)
        monkeypatch.setattr("apps.learning_worker_runtime._write_learning_worker_record", fake_write_record)
        monkeypatch.setattr(daemon_tasks, "_run_claimed_learning_job", fake_run_claimed_job)

        tick_at = 0.0

        async def ticker(started_at: float) -> None:
            nonlocal tick_at
            await asyncio.sleep(0.05)
            tick_at = time.perf_counter() - started_at

        async def run_loop() -> None:
            started_at = time.perf_counter()
            await asyncio.gather(
                daemon_tasks.learning_worker_loop(
                    state_dir=tmp_path,
                    is_running=lambda: running,
                    idle_seconds=1.0,
                ),
                ticker(started_at),
            )

        asyncio.run(run_loop())

        assert tick_at < 0.15
